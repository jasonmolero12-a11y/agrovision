"""
Views da app propriedades - CRUD de Propriedades, Talhões e Culturas.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme

from contas.decorators import acesso_tecnico, admin_required, perfil_required
from .models import Propriedade, Talhao, Cultura, RegistoProducao, PedidoCompra


def _propriedades_visiveis(user):
    if user.is_admin or user.is_superuser:
        return Propriedade.objects.all()
    if user.is_consultor:
        return Propriedade.objects.filter(consultor_responsavel=user)
    if user.is_tecnico:
        return Propriedade.objects.filter(tecnico_responsavel=user)
    if user.is_analista:
        return Propriedade.objects.filter(analista_responsavel=user)
    if user.is_agricultor:
        return Propriedade.objects.filter(proprietario=user)
    if user.is_cliente:
        return Propriedade.objects.filter(clientes_autorizados=user)
    return Propriedade.objects.none()


def _previsao_producao(propriedade):
    """Previsão estatística explicável usando apenas dados reais registados."""
    from decimal import Decimal
    from meteorologia.models import RegistroClima
    from consultoria.models import PragaDoenca

    registos = list(RegistoProducao.objects.filter(
        talhao__propriedade=propriedade
    ).order_by('-data_colheita', '-pk')[:5])
    if not registos:
        return {'disponivel': False, 'mensagem': 'Registe pelo menos uma colheita para iniciar a previsão.'}

    unidade = registos[0].unidade
    serie = [r for r in reversed(registos) if r.unidade == unidade]
    valores = [Decimal(r.quantidade) for r in serie]
    pesos = list(range(1, len(valores) + 1))
    media_ponderada = sum(v * p for v, p in zip(valores, pesos)) / Decimal(sum(pesos))
    tendencia = (valores[-1] - valores[0]) / Decimal(max(1, len(valores) - 1)) if len(valores) > 1 else Decimal('0')
    previsao_base = max(Decimal('0'), media_ponderada + tendencia * Decimal('0.5'))

    fatores = [f'Média ponderada de {len(valores)} colheita(s) em {unidade}.']
    ajuste = Decimal('1')
    clima = RegistroClima.objects.filter(propriedade=propriedade).order_by('-data').first()
    if clima:
        if clima.temperatura is not None and clima.temperatura >= 35:
            ajuste -= Decimal('0.07'); fatores.append('Temperatura recente ≥ 35°C: ajuste de -7%.')
        if clima.humidade is not None and clima.humidade >= 85:
            ajuste -= Decimal('0.05'); fatores.append('Humidade recente ≥ 85%: ajuste de -5%.')
    pragas_ativas = PragaDoenca.objects.filter(talhao__propriedade=propriedade, resolvido=False)
    graves = pragas_ativas.filter(severidade__in=['alta', 'critica']).count()
    if graves:
        reducao = min(Decimal('0.20'), Decimal('0.05') * graves)
        ajuste -= reducao
        fatores.append(f'{graves} praga(s) grave(s) ativa(s): ajuste de -{int(reducao * 100)}%.')
    if ajuste == 1:
        fatores.append('Sem fatores negativos recentes registados.')

    previsao_ajustada = max(Decimal('0'), previsao_base * ajuste)
    confianca = 'alta' if len(valores) >= 5 else ('média' if len(valores) >= 3 else 'baixa')
    return {
        'disponivel': True, 'valor': round(previsao_ajustada, 2), 'valor_base': round(previsao_base, 2),
        'unidade': unidade, 'confianca': confianca, 'amostras': len(valores),
        'tendencia': round(tendencia, 2), 'fatores': fatores,
        'aviso': 'Estimativa de apoio à decisão; deve ser validada por um técnico agrónomo.',
    }


# ==========================================================================
# PROPRIEDADES
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor', 'cliente')
def lista_propriedades(request):
    """Lista as propriedades conforme o perfil do utilizador."""
    propriedades = _propriedades_visiveis(request.user)
    busca = request.GET.get('q', '').strip()
    if busca:
        propriedades = propriedades.filter(
            Q(nome__icontains=busca) |
            Q(localizacao__icontains=busca) |
            Q(proprietario__nome_completo__icontains=busca) |
            Q(consultor_responsavel__nome_completo__icontains=busca)
        )

    return render(request, 'propriedades/lista.html', {'propriedades': propriedades, 'filtros': {'q': busca}})


@login_required
@perfil_required('cliente')
def mercado_agricola(request):
    propriedades = Propriedade.objects.filter(exposta_para_clientes=True).select_related('proprietario').prefetch_related('talhoes__cultura', 'talhoes__registos_producao', 'favoritada_por')
    filtros = {chave: request.GET.get(chave, '').strip() for chave in ('q', 'cultura', 'provincia', 'unidade', 'estado', 'quantidade_min')}
    if filtros['q']:
        propriedades = propriedades.filter(Q(nome__icontains=filtros['q']) | Q(localizacao__icontains=filtros['q']) | Q(descricao_comercial__icontains=filtros['q']) | Q(talhoes__cultura__nome__icontains=filtros['q']))
    if filtros['cultura']: propriedades = propriedades.filter(talhoes__cultura_id=filtros['cultura'])
    if filtros['provincia']: propriedades = propriedades.filter(localizacao__icontains=filtros['provincia'])
    if filtros['unidade']: propriedades = propriedades.filter(talhoes__registos_producao__unidade=filtros['unidade'])
    if filtros['estado']: propriedades = propriedades.filter(talhoes__registos_producao__estado_comercial=filtros['estado'])
    if filtros['quantidade_min']:
        try: propriedades = propriedades.filter(talhoes__registos_producao__quantidade__gte=filtros['quantidade_min'])
        except (TypeError, ValueError): pass
    if request.GET.get('favoritos') == '1': propriedades = propriedades.filter(favoritada_por=request.user)
    propriedades = propriedades.distinct()
    for propriedade in propriedades:
        ofertas = sorted((r for t in propriedade.talhoes.all() for r in t.registos_producao.all()), key=lambda r: r.data_colheita, reverse=True)
        propriedade.oferta_principal = ofertas[0] if ofertas else None
        propriedade.eh_favorita = request.user in propriedade.favoritada_por.all()
    pagina = Paginator(list(propriedades), 9).get_page(request.GET.get('pagina'))
    return render(request, 'propriedades/mercado.html', {'propriedades': pagina, 'pagina': pagina, 'filtros': filtros, 'somente_favoritos': request.GET.get('favoritos') == '1', 'culturas': Cultura.objects.all(), 'estados': RegistoProducao.ESTADO_COMERCIAL_CHOICES, 'unidades': RegistoProducao.UNIDADE_CHOICES})


@login_required
@perfil_required('cliente')
def favoritar_mercado(request, pk):
    propriedade = get_object_or_404(Propriedade, pk=pk, exposta_para_clientes=True)
    if request.method == 'POST':
        if propriedade.favoritada_por.filter(pk=request.user.pk).exists(): propriedade.favoritada_por.remove(request.user)
        else: propriedade.favoritada_por.add(request.user)
    destino = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = reverse('propriedades:mercado')
    return redirect(destino)


@login_required
@perfil_required('cliente')
def comparar_mercado(request):
    ids = request.GET.getlist('itens')[:3]
    propriedades = Propriedade.objects.filter(pk__in=ids, exposta_para_clientes=True).prefetch_related('talhoes__cultura', 'talhoes__registos_producao')
    for propriedade in propriedades:
        ofertas = sorted((r for t in propriedade.talhoes.all() for r in t.registos_producao.all()), key=lambda r: r.data_colheita, reverse=True)
        propriedade.oferta_principal = ofertas[0] if ofertas else None
    return render(request, 'propriedades/mercado_comparar.html', {'propriedades': propriedades})


@login_required
@perfil_required('cliente')
def detalhe_mercado(request, pk):
    propriedade = get_object_or_404(Propriedade.objects.filter(exposta_para_clientes=True).select_related('proprietario'), pk=pk)
    producoes = RegistoProducao.objects.filter(talhao__propriedade=propriedade).select_related('talhao__cultura')[:12]
    return render(request, 'propriedades/mercado_detalhe.html', {'propriedade': propriedade, 'producoes': producoes, 'eh_favorita': propriedade.favoritada_por.filter(pk=request.user.pk).exists()})


@login_required
@perfil_required('cliente')
def solicitar_compra(request, pk):
    """Cria um pedido que precisa da confirmação do agricultor e aprovação do admin."""
    propriedade = get_object_or_404(Propriedade, pk=pk, exposta_para_clientes=True)
    producoes = RegistoProducao.objects.filter(
        talhao__propriedade=propriedade, estado_comercial='disponivel'
    ).select_related('talhao__cultura').order_by('-data_colheita')
    if request.method == 'POST':
        producao_id = request.POST.get('producao')
        producao = get_object_or_404(producoes, pk=producao_id) if producao_id else None
        contacto = request.POST.get('contacto', '').strip() or request.user.telefone or request.user.email
        pedido = PedidoCompra.objects.create(
            cliente=request.user, propriedade=propriedade, producao=producao,
            quantidade_pretendida=request.POST.get('quantidade', '').strip(),
            contacto=contacto, observacoes=request.POST.get('observacoes', '').strip(),
        )
        messages.success(request, 'Pedido enviado. O administrador contactará o agricultor antes de decidir e liberar o acesso.')
        return redirect('propriedades:pedidos_compra')
    return render(request, 'propriedades/solicitar_compra.html', {'propriedade': propriedade, 'producoes': producoes})


@login_required
def pedidos_compra(request):
    if request.user.is_admin or request.user.is_superuser:
        pedidos = PedidoCompra.objects.all()
    elif request.user.is_agricultor:
        pedidos = PedidoCompra.objects.filter(propriedade__proprietario=request.user)
    elif request.user.is_cliente:
        pedidos = PedidoCompra.objects.filter(cliente=request.user)
    else:
        messages.error(request, 'Não tem permissão para consultar pedidos de compra.')
        return redirect('dashboard:home')
    pedidos = pedidos.select_related('cliente', 'propriedade', 'propriedade__proprietario', 'producao__talhao__cultura')
    return render(request, 'propriedades/pedidos_compra.html', {'pedidos': pedidos})


@login_required
def responder_pedido_compra(request, pk):
    pedido = get_object_or_404(PedidoCompra.objects.select_related('propriedade', 'cliente'), pk=pk)
    if request.method != 'POST':
        return redirect('propriedades:pedidos_compra')
    acao = request.POST.get('acao')
    nota = request.POST.get('nota', '').strip()
    if request.user.is_agricultor and pedido.propriedade.proprietario_id == request.user.pk:
        if pedido.status != 'aguarda_agricultor':
            messages.error(request, 'Este pedido ainda não aguarda a sua confirmação.')
        elif acao == 'confirmar':
            pedido.resposta_agricultor = True
            pedido.observacao_agricultor = nota
            pedido.status = 'confirmado'
            pedido.save()
            messages.success(request, 'Disponibilidade confirmada. O administrador já pode aprovar o pedido.')
        elif acao == 'recusar':
            pedido.resposta_agricultor = False
            pedido.observacao_agricultor = nota
            pedido.status = 'recusado'
            pedido.save()
            messages.success(request, 'Indisponibilidade registada.')
        return redirect('propriedades:pedidos_compra')
    if request.user.is_admin or request.user.is_superuser:
        pedido.nota_administracao = nota
        pedido.decidido_por = request.user
        if acao == 'contactar':
            pedido.status = 'aguarda_agricultor'
            pedido.save()
            messages.success(request, 'Pedido encaminhado para confirmação do agricultor.')
        elif acao == 'aprovar':
            if pedido.resposta_agricultor is not True:
                messages.error(request, 'Só é possível aprovar depois da confirmação do agricultor.')
            else:
                pedido.status = 'aprovado'
                pedido.save()
                pedido.propriedade.clientes_autorizados.add(pedido.cliente)
                messages.success(request, 'Compra aprovada e cliente autorizado na propriedade.')
        elif acao == 'recusar':
            pedido.status = 'recusado'
            pedido.save()
            messages.success(request, 'Pedido recusado pela administração.')
        return redirect('propriedades:pedidos_compra')
    messages.error(request, 'Não tem permissão para alterar este pedido.')
    return redirect('dashboard:home')


@login_required
@perfil_required('admin', 'agricultor')
def nova_propriedade(request):
    """Admin cria para qualquer agricultor; agricultor cria apenas para si."""
    from contas.models import Utilizador
    if request.method == 'POST':
        prop = Propriedade(
            nome=request.POST.get('nome', ''),
            proprietario=request.user if request.user.is_agricultor else None,
            consultor_responsavel_id=(request.POST.get('consultor') or None) if request.user.is_admin else None,
            tecnico_responsavel_id=(request.POST.get('tecnico') or None) if request.user.is_admin else None,
            analista_responsavel_id=(request.POST.get('analista') or None) if request.user.is_admin else None,
            localizacao=request.POST.get('localizacao', ''),
            area_total=request.POST.get('area_total') or None,
            foto_capa=request.FILES.get('foto_capa'),
            exposta_para_clientes=request.POST.get('exposta_para_clientes') == 'on',
            descricao_comercial=request.POST.get('descricao_comercial', '').strip(),
        )
        if request.user.is_admin or request.user.is_superuser:
            prop.proprietario_id = request.POST.get('proprietario')
        try:
            prop.save()
            if request.user.is_admin or request.user.is_superuser:
                prop.clientes_autorizados.set(request.POST.getlist('clientes_autorizados'))
            if request.user.is_agricultor:
                messages.success(request, 'Propriedade criada. A administração já pode atribuir a equipa que fará o acompanhamento.')
            else:
                messages.success(request, 'Propriedade criada com sucesso!')
            return redirect('propriedades:lista')
        except Exception as e:
            messages.error(request, f'Erro ao criar: {e}')

    agricultores = Utilizador.objects.filter(tipo_utilizador='agricultor', is_active=True)
    clientes = Utilizador.objects.filter(tipo_utilizador='cliente', is_active=True)
    consultores = Utilizador.objects.filter(tipo_utilizador='consultor', is_active=True)
    tecnicos = Utilizador.objects.filter(tipo_utilizador='tecnico', is_active=True)
    analistas = Utilizador.objects.filter(tipo_utilizador='analista', is_active=True)
    return render(request, 'propriedades/form.html', {
        'titulo': 'Nova Propriedade',
        'agricultores': agricultores,
        'clientes': clientes,
        'consultores': consultores,
        'tecnicos': tecnicos,
        'analistas': analistas,
        'edicao_agricultor': request.user.is_agricultor,
    })


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor', 'cliente')
def detalhe_propriedade(request, pk):
    """Mostra os detalhes de uma propriedade e os seus talhões."""
    propriedade = get_object_or_404(_propriedades_visiveis(request.user), pk=pk)
    talhoes = propriedade.talhoes.all()
    producoes = RegistoProducao.objects.filter(talhao__propriedade=propriedade).select_related('talhao')
    previsao_producao = _previsao_producao(propriedade)
    if request.user.is_cliente:
        return render(request, 'propriedades/detalhe_cliente.html', {
            'propriedade': propriedade, 'producoes': producoes,
        })
    return render(request, 'propriedades/detalhe.html', {
        'propriedade': propriedade,
        'talhoes': talhoes,
        'producoes': producoes,
        'previsao_producao': previsao_producao,
    })


@login_required
@perfil_required('admin', 'agricultor')
def editar_propriedade(request, pk):
    """Edita uma propriedade existente."""
    from contas.models import Utilizador
    propriedade = get_object_or_404(_propriedades_visiveis(request.user), pk=pk)
    if request.method == 'POST':
        propriedade.nome = request.POST.get('nome', propriedade.nome)
        if request.user.is_admin or request.user.is_superuser:
            propriedade.proprietario_id = request.POST.get('proprietario', propriedade.proprietario_id)
            propriedade.consultor_responsavel_id = request.POST.get('consultor') or None
            propriedade.tecnico_responsavel_id = request.POST.get('tecnico') or None
            propriedade.analista_responsavel_id = request.POST.get('analista') or None
        propriedade.localizacao = request.POST.get('localizacao', propriedade.localizacao)
        propriedade.area_total = request.POST.get('area_total') or None
        propriedade.exposta_para_clientes = request.POST.get('exposta_para_clientes') == 'on'
        propriedade.descricao_comercial = request.POST.get('descricao_comercial', '').strip()
        if request.FILES.get('foto_capa'):
            propriedade.foto_capa = request.FILES['foto_capa']
        propriedade.save()
        if request.user.is_admin or request.user.is_superuser:
            propriedade.clientes_autorizados.set(request.POST.getlist('clientes_autorizados'))
        messages.success(request, 'Propriedade atualizada!')
        return redirect('propriedades:detalhe', pk=propriedade.pk)

    agricultores = Utilizador.objects.filter(tipo_utilizador='agricultor', is_active=True)
    clientes = Utilizador.objects.filter(tipo_utilizador='cliente', is_active=True)
    consultores = Utilizador.objects.filter(tipo_utilizador='consultor', is_active=True)
    tecnicos = Utilizador.objects.filter(tipo_utilizador='tecnico', is_active=True)
    analistas = Utilizador.objects.filter(tipo_utilizador='analista', is_active=True)
    return render(request, 'propriedades/form.html', {
        'titulo': 'Editar Propriedade',
        'propriedade': propriedade,
        'agricultores': agricultores,
        'clientes': clientes,
        'consultores': consultores,
        'tecnicos': tecnicos,
        'analistas': analistas,
        'edicao_agricultor': request.user.is_agricultor,
    })


@login_required
@admin_required
def eliminar_propriedade(request, pk):
    """Elimina uma propriedade."""
    propriedade = get_object_or_404(_propriedades_visiveis(request.user), pk=pk)
    if request.method == 'POST':
        propriedade.delete()
        messages.success(request, 'Propriedade eliminada.')
        return redirect('propriedades:lista')
    return render(request, 'propriedades/confirmar_eliminar.html', {'propriedade': propriedade})


# ==========================================================================
# TALHÕES
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_talhoes(request):
    """Lista todos os talhões."""
    talhoes = Talhao.objects.select_related('propriedade', 'cultura').filter(
        propriedade__in=_propriedades_visiveis(request.user)
    )
    busca = request.GET.get('q', '').strip()
    if busca:
        talhoes = talhoes.filter(
            Q(nome__icontains=busca) |
            Q(propriedade__nome__icontains=busca) |
            Q(cultura__nome__icontains=busca) |
            Q(tipo_solo__icontains=busca)
        )
    return render(request, 'propriedades/lista_talhoes.html', {'talhoes': talhoes, 'filtros': {'q': busca}})


@login_required
@perfil_required('admin', 'agricultor')
def novo_talhao(request):
    """Cria um novo talhão."""
    if request.method == 'POST':
        propriedade = get_object_or_404(_propriedades_visiveis(request.user), pk=request.POST.get('propriedade'))
        talhao = Talhao(
            propriedade=propriedade,
            nome=request.POST.get('nome', ''),
            cultura=_obter_ou_criar_cultura(request.POST.get('cultura_nome')),
            area=request.POST.get('area') or None,
            tipo_solo=request.POST.get('tipo_solo', ''),
            data_plantio=request.POST.get('data_plantio') or None,
            estadio_fenologico=request.POST.get('estadio_fenologico', ''),
            foto_atual=request.FILES.get('foto_atual'),
        )
        talhao.save()
        messages.success(request, 'Talhão criado com sucesso!')
        return redirect('propriedades:lista_talhoes')

    propriedades = _propriedades_visiveis(request.user)
    culturas = Cultura.objects.all()
    return render(request, 'propriedades/form_talhao.html', {
        'titulo': 'Novo Talhão',
        'propriedades': propriedades,
        'culturas': culturas,
    })


@login_required
@perfil_required('admin', 'agricultor')
def editar_talhao(request, pk):
    talhao = get_object_or_404(
        Talhao.objects.filter(propriedade__in=_propriedades_visiveis(request.user)), pk=pk
    )
    propriedades = _propriedades_visiveis(request.user)
    if request.method == 'POST':
        talhao.propriedade = get_object_or_404(propriedades, pk=request.POST.get('propriedade'))
        talhao.nome = request.POST.get('nome', '').strip()
        talhao.cultura = _obter_ou_criar_cultura(request.POST.get('cultura_nome'))
        talhao.area = request.POST.get('area') or None
        talhao.tipo_solo = request.POST.get('tipo_solo', '').strip()
        talhao.data_plantio = request.POST.get('data_plantio') or None
        talhao.estadio_fenologico = request.POST.get('estadio_fenologico', '').strip()
        if request.FILES.get('foto_atual'):
            talhao.foto_atual = request.FILES['foto_atual']
        talhao.save()
        messages.success(request, 'Talhão atualizado com sucesso.')
        return redirect('propriedades:lista_talhoes')
    return render(request, 'propriedades/form_talhao.html', {
        'titulo': 'Editar Talhão', 'talhao': talhao,
        'propriedades': propriedades, 'culturas': Cultura.objects.all(),
    })


# ==========================================================================
# CULTURAS
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_culturas(request):
    """Lista todas as culturas."""
    culturas = Cultura.objects.all()
    return render(request, 'propriedades/lista_culturas.html', {'culturas': culturas})


@login_required
@acesso_tecnico
def nova_cultura(request):
    """Cria uma nova cultura."""
    if request.method == 'POST':
        Cultura.objects.create(
            nome=request.POST.get('nome', ''),
            ciclo=request.POST.get('ciclo', ''),
            epoca_plantio=request.POST.get('epoca_plantio', ''),
            descricao=request.POST.get('descricao', ''),
            imagem_referencia=request.FILES.get('imagem_referencia'),
        )
        messages.success(request, 'Cultura criada com sucesso!')
        return redirect('propriedades:lista_culturas')

    return render(request, 'propriedades/form_cultura.html', {'titulo': 'Nova Cultura'})


@login_required
@perfil_required('admin', 'consultor', 'tecnico', 'agricultor')
def novo_registo_producao(request, propriedade_pk):
    """Regista uma colheita real ligada a um talhão autorizado."""
    propriedade = get_object_or_404(_propriedades_visiveis(request.user), pk=propriedade_pk)
    talhoes = propriedade.talhoes.all()
    if request.method == 'POST':
        talhao = get_object_or_404(talhoes, pk=request.POST.get('talhao'))
        RegistoProducao.objects.create(
            talhao=talhao,
            campanha=request.POST.get('campanha', ''),
            data_colheita=request.POST.get('data_colheita'),
            quantidade=request.POST.get('quantidade'),
            unidade=request.POST.get('unidade', 'kg'),
            estado_comercial=request.POST.get('estado_comercial', 'disponivel'),
            qualidade=request.POST.get('qualidade', ''),
            observacoes=request.POST.get('observacoes', ''),
            foto_colheita=request.FILES.get('foto_colheita'),
        )
        messages.success(request, 'Produção/colheita registada com sucesso.')
        return redirect('propriedades:detalhe', pk=propriedade.pk)
    return render(request, 'propriedades/form_producao.html', {'propriedade': propriedade, 'talhoes': talhoes})
def _obter_ou_criar_cultura(nome):
    """Transforma o texto livre do talhão num cadastro de cultura reutilizável."""
    nome = ' '.join((nome or '').strip().split())
    if not nome:
        return None
    existente = Cultura.objects.filter(nome__iexact=nome).first()
    if existente:
        return existente
    return Cultura.objects.create(nome=nome, ciclo='Não informado')
