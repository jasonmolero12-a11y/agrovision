"""
Views da app consultoria - Recomendações, Visitas Técnicas e Pragas/Doenças.
Inclui geração de PDF (Reportlab) para recomendações.
"""

import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.urls import reverse

from contas.decorators import acesso_tecnico, perfil_required
from config_sistema.ia import gerar_texto_ia
from propriedades.models import Propriedade, Talhao
from .models import Recomendacao, VisitaTecnica, FotoVisita, PragaDoenca
from meteorologia.models import RegistroClima, Alerta
from meteorologia.views import obter_previsao_api, _guardar_registo_e_alerta


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


def _recomendacoes_visiveis(user):
    recomendacoes = Recomendacao.objects.filter(talhao__propriedade__in=_propriedades_visiveis(user))
    if user.is_cliente or user.is_agricultor:
        recomendacoes = recomendacoes.filter(status__in=['emitida', 'aplicada'])
    return recomendacoes


def _visitas_visiveis(user):
    if user.is_consultor:
        return VisitaTecnica.objects.filter(
            Q(responsavel=user)
            | Q(propriedade__consultor_responsavel=user)
        ).distinct()
    if user.is_tecnico:
        return VisitaTecnica.objects.filter(responsavel=user)
    return VisitaTecnica.objects.filter(propriedade__in=_propriedades_visiveis(user))


def _risco_talhao(talhao):
    """Calcula risco agronomico simples por regras para apoiar a defesa."""
    propriedade = talhao.propriedade
    ultimo_clima = RegistroClima.objects.filter(propriedade=propriedade).order_by('-data').first()
    pragas_ativas = PragaDoenca.objects.filter(talhao=talhao, resolvido=False)
    alertas_ativos = Alerta.objects.filter(propriedade=propriedade, lido=False)

    pontos = 10
    fatores = []

    if ultimo_clima:
        if ultimo_clima.temperatura is not None and float(ultimo_clima.temperatura) >= 35:
            pontos += 30
            fatores.append('temperatura elevada')
        if ultimo_clima.humidade is not None and float(ultimo_clima.humidade) <= 35:
            pontos += 20
            fatores.append('humidade baixa')
        if ultimo_clima.vento_velocidade is not None and float(ultimo_clima.vento_velocidade) >= 40:
            pontos += 15
            fatores.append('vento forte')
    else:
        fatores.append('sem historico climatico recente')

    severidades = {'baixa': 8, 'media': 16, 'alta': 25, 'critica': 35}
    for praga in pragas_ativas[:4]:
        pontos += severidades.get(praga.severidade, 8)
        fatores.append(f'praga/doenca: {praga.nome} ({praga.get_severidade_display()})')

    if alertas_ativos.exists():
        pontos += min(alertas_ativos.count() * 8, 24)
        fatores.append(f'{alertas_ativos.count()} alerta(s) ativo(s)')

    pontos = min(pontos, 100)
    if pontos >= 75:
        nivel = 'Critico'
        prioridade = 'urgente'
    elif pontos >= 55:
        nivel = 'Alto'
        prioridade = 'alta'
    elif pontos >= 30:
        nivel = 'Medio'
        prioridade = 'media'
    else:
        nivel = 'Baixo'
        prioridade = 'baixa'

    if not fatores:
        fatores.append('condicoes normais')

    return {
        'pontos': pontos,
        'nivel': nivel,
        'prioridade': prioridade,
        'fatores': fatores,
        'ultimo_clima': ultimo_clima,
    }


def _sugestao_recomendacao(talhao, risco):
    cultura = talhao.cultura.nome if talhao.cultura else 'cultura definida no talhao'
    fatores = '; '.join(risco['fatores'])
    linhas = [
        f"Risco agronomico estimado: {risco['nivel']} ({risco['pontos']}/100).",
        f"Talhao: {talhao.nome} | Cultura: {cultura}.",
        f"Fatores observados: {fatores}.",
        "Acao recomendada: realizar vistoria tecnica, confirmar as condicoes em campo e ajustar o manejo conforme a cultura.",
    ]

    if risco['nivel'] in ['Alto', 'Critico']:
        linhas.append("Priorizar intervencao imediata e monitorar a evolucao nas proximas 24-48 horas.")
    elif risco['nivel'] == 'Medio':
        linhas.append("Manter monitoramento regular e preparar medida corretiva caso o risco aumente.")
    else:
        linhas.append("Manter acompanhamento preventivo e atualizar os dados climaticos periodicamente.")

    return '\n'.join(linhas)


def _sugestao_recomendacao_automatica(talhao, risco, dados_solo_extra="", dados_clima_extra=""):
    ultimo_clima = risco.get('ultimo_clima')
    clima = 'Sem registo climático recente.'
    if ultimo_clima:
        clima = (
            f"Temperatura: {ultimo_clima.temperatura} C; "
            f"humidade: {ultimo_clima.humidade}%; vento: {ultimo_clima.vento_velocidade} km/h; "
            f"condição: {ultimo_clima.descricao}."
        )
    pragas = PragaDoenca.objects.filter(talhao=talhao, resolvido=False).order_by('-data_deteccao')[:5]
    pragas_txt = '; '.join(f'{p.nome} ({p.get_severidade_display()})' for p in pragas) or 'Sem pragas ativas registadas.'
    contexto = (
        f"Propriedade: {talhao.propriedade.nome}. Localização: {talhao.propriedade.localizacao}. "
        f"Talhão: {talhao.nome}. Cultura: {talhao.cultura or 'não definida'}. "
        f"Área: {talhao.area or 'não informada'} ha. Solo: {talhao.tipo_solo or 'não informado'}. "
        f"Clima: {clima} Pragas/doenças: {pragas_txt}. "
        f"Risco por regras internas: {risco['nivel']} ({risco['pontos']}/100). "
        f"Fatores: {', '.join(risco['fatores'])}. "
        f"Dados adicionais do solo informados no pedido: {dados_solo_extra or 'não informados'}. "
        f"Dados adicionais do clima informados no pedido: {dados_clima_extra or 'não informados'}."
    )
    prompt = (
        "Gere uma recomendação agronómica operacional para o consultor rever. "
        "Inclua: diagnóstico, ação recomendada, prioridade e observações de acompanhamento."
    )
    return gerar_texto_ia(prompt, contexto=contexto) or _sugestao_recomendacao(talhao, risco)


def _possiveis_doencas_api(talhao, dados_clima):
    """Levanta hipóteses preventivas; não substitui diagnóstico de campo."""
    cultura = str(talhao.cultura or '').lower()
    humidade = float(dados_clima.get('humidade') or 0)
    temperatura = float(dados_clima.get('temperatura') or 0)
    chuva = float(dados_clima.get('precipitacao') or 0)
    possibilidades = []

    if humidade >= 75 or chuva >= 5:
        nome = 'doenças fúngicas e manchas foliares'
        if 'milho' in cultura:
            nome = 'ferrugem ou mancha foliar do milho'
        elif 'tomate' in cultura:
            nome = 'míldio ou pinta-preta do tomateiro'
        elif 'feij' in cultura:
            nome = 'antracnose ou ferrugem do feijoeiro'
        possibilidades.append({
            'nome': nome,
            'motivo': 'A humidade ou precipitação favorece a permanência de água nas folhas.',
            'sinais': 'Procure manchas, pó semelhante a ferrugem, amarelecimento ou folhas que secam.',
            'acao': 'Melhore ventilação e drenagem, evite molhar folhas no fim do dia e peça confirmação ao técnico antes de aplicar qualquer produto.',
        })
    if chuva >= 10:
        possibilidades.append({
            'nome': 'podridão radicular',
            'motivo': 'Chuva elevada pode deixar o solo encharcado e reduzir o oxigénio nas raízes.',
            'sinais': 'Observe murcha mesmo com solo molhado, raízes escuras, mau cheiro ou crescimento fraco.',
            'acao': 'Verifique a drenagem, não aumente a rega e solicite inspeção das raízes e do solo.',
        })
    if temperatura >= 32 and humidade >= 70:
        possibilidades.append({
            'nome': 'doenças bacterianas favorecidas por calor e humidade',
            'motivo': 'A combinação de calor e humidade pode acelerar algumas infeções.',
            'sinais': 'Procure lesões húmidas, escurecimento, mau cheiro ou murcha localizada.',
            'acao': 'Isole plantas muito afetadas, higienize ferramentas e peça diagnóstico antes do tratamento.',
        })
    if not possibilidades:
        possibilidades.append({
            'nome': 'nenhuma possibilidade climática forte identificada',
            'motivo': 'Os valores atuais não ultrapassaram as regras preventivas de humidade, chuva e calor.',
            'sinais': 'Continue a observar folhas, caule, frutos e raízes durante as visitas.',
            'acao': 'Registe fotografia e sintomas se surgir alguma alteração; clima favorável não elimina a possibilidade de doença.',
        })
    return possibilidades[:3]


def _explicar_resultado_api(talhao, dados_clima, risco):
    """Transforma números da API e regras internas numa explicação clara ao agricultor."""
    local = dados_clima.get('cidade') or talhao.propriedade.localizacao or 'localização informada'
    provincia = dados_clima.get('provincia')
    area = f'{local}, {provincia}' if provincia and provincia.lower() not in local.lower() else local
    temperatura = dados_clima.get('temperatura')
    humidade = dados_clima.get('humidade')
    vento = dados_clima.get('vento')
    chuva = dados_clima.get('precipitacao', 0)
    cultura = str(talhao.cultura or 'cultura ainda não identificada')
    fatores = ', '.join(risco['fatores'])
    if risco['nivel'] in ('Alto', 'Critico'):
        acao = 'Peça uma vistoria prioritária à equipa técnica e evite decisões irreversíveis antes da confirmação em campo.'
    elif risco['nivel'] == 'Medio':
        acao = 'Acompanhe o talhão diariamente e peça validação técnica caso os sinais piorem.'
    else:
        acao = 'Mantenha o manejo preventivo e atualize clima, pragas e estado da cultura regularmente.'
    return (
        f'A análise foi feita para {area}, no talhão {talhao.nome}, com a cultura {cultura}. '
        f'O AgroVision consultou os dados meteorológicos e encontrou {temperatura} graus Celsius, humidade de {humidade} por cento, '
        f'vento de {vento} quilómetros por hora e precipitação de {chuva} milímetros. '
        f'Combinando estes dados com solo, cultura, pragas e alertas registados, o AgroVision '
        f'classificou o risco como {risco["nivel"]}, com {risco["pontos"]} pontos em cem. '
        f'Os fatores considerados foram: {fatores}. {acao} '
        'Esta explicação é uma orientação automática. A recomendação oficial só é publicada depois da revisão do consultor.'
    )


@login_required
@perfil_required('agricultor')
def consultoria_api_agricultor(request):
    """Gera orientação preliminar com clima real e dados do talhão do agricultor."""
    talhoes = Talhao.objects.filter(propriedade__proprietario=request.user).select_related(
        'propriedade', 'propriedade__consultor_responsavel', 'propriedade__tecnico_responsavel',
        'propriedade__analista_responsavel', 'cultura')
    talhao = dados_clima = risco = None
    orientacao = ''
    explicacao_resultado = ''
    possiveis_doencas = []
    talhao_id = request.POST.get('talhao') if request.method == 'POST' else request.GET.get('talhao')
    if talhao_id:
        talhao = get_object_or_404(talhoes, pk=talhao_id)
    elif talhoes.exists():
        talhao = talhoes.first()
    if request.method == 'POST':
        if not talhao:
            messages.error(request, 'Crie uma propriedade e um talhão antes de solicitar a consultoria.')
        else:
            propriedade = talhao.propriedade
            local = (propriedade.localizacao or '').strip()
            if not local:
                messages.error(request, 'Informe a localização da propriedade para consultar a meteorologia real.')
            else:
                dados_clima = None
                # Endereços angolanos novos nem sempre são encontrados sem o
                # país. Tentamos formas progressivas sem alterar o que o
                # agricultor escreveu na propriedade.
                candidatos_local = [local]
                if 'angola' not in local.lower():
                    candidatos_local.append(f'{local}, Angola')
                partes = [parte.strip() for parte in local.split(',') if parte.strip()]
                if len(partes) > 1:
                    candidatos_local.extend([partes[-1], f'{partes[-1]}, Angola'])
                local_simplificado = local
                for prefixo_local in (
                    'Província de ', 'Provincia de ', 'Município de ',
                    'Municipio de ', 'Comuna de ', 'Fazenda ',
                ):
                    local_simplificado = local_simplificado.replace(prefixo_local, '')
                if local_simplificado != local:
                    candidatos_local.extend([
                        local_simplificado,
                        f'{local_simplificado}, Angola',
                    ])
                for local_consulta in dict.fromkeys(candidatos_local):
                    dados_clima = obter_previsao_api(local_consulta)
                    if dados_clima and not dados_clima.get('erro'):
                        break
                if not dados_clima:
                    messages.error(
                        request,
                        f'O AgroVision não encontrou a localização "{local}". '
                        'Na propriedade, informe município, província e país; '
                        'por exemplo: Cacuaco, Luanda, Angola.',
                    )
                elif dados_clima.get('erro'):
                    messages.error(request, dados_clima['erro'])
                else:
                    _guardar_registo_e_alerta(propriedade, dados_clima)
                    risco = _risco_talhao(talhao)
                    resumo = dados_clima.get('resumo_7_dias') or {}
                    clima = (
                        f"Fonte meteorológica usada pelo AgroVision: {dados_clima.get('provedor', 'serviço meteorológico')}; local: {dados_clima.get('cidade', local)}; "
                        f"condição: {dados_clima.get('descricao', 'não informada')}; temperatura: {dados_clima.get('temperatura')} graus Celsius; "
                        f"humidade: {dados_clima.get('humidade')} por cento; vento: {dados_clima.get('vento')} quilómetros por hora; "
                        f"precipitação: {dados_clima.get('precipitacao', 0)} milímetros; chuva em sete dias: {resumo.get('chuva_total', 'não informada')} milímetros.")
                    solo = f"Tipo de solo registado: {talhao.tipo_solo}." if talhao.tipo_solo else 'Sem tipo de solo registado; confirmar com análise laboratorial.'
                    orientacao = _sugestao_recomendacao_automatica(talhao, risco, dados_solo_extra=solo, dados_clima_extra=clima)
                    explicacao_resultado = _explicar_resultado_api(talhao, dados_clima, risco)
                    possiveis_doencas = _possiveis_doencas_api(talhao, dados_clima)
                    if request.POST.get('acao') == 'solicitar_recomendacao':
                        consultor = propriedade.consultor_responsavel
                        if not consultor:
                            messages.error(request, 'A administração ainda precisa atribuir um consultor a esta propriedade.')
                        else:
                            prefixo = 'Análise AgroVision solicitada pelo agricultor para revisão.\n'
                            rascunho = Recomendacao.objects.filter(
                                talhao=talhao, consultor=consultor, status='rascunho',
                                texto_recomendacao__startswith=prefixo.strip(),
                            ).first()
                            if not rascunho:
                                rascunho = Recomendacao(talhao=talhao, consultor=consultor, status='rascunho')
                            rascunho.dados_solo = solo
                            rascunho.dados_clima = clima
                            rascunho.texto_recomendacao = prefixo + orientacao
                            rascunho.prioridade = risco['prioridade']
                            rascunho.save()
                            messages.success(request, 'Análise enviada ao consultor como rascunho. Ela só aparecerá como recomendação oficial depois da revisão e emissão.')
                            return redirect('consultoria:consultoria_api_agricultor')
                    messages.success(request, 'Consultoria preliminar atualizada com dados meteorológicos reais.')
    analise_pendente = None
    ultima_resposta = None
    if talhao:
        analise_pendente = Recomendacao.objects.filter(
            talhao=talhao,
            status='rascunho',
            texto_recomendacao__startswith='Análise AgroVision solicitada',
        ).select_related('consultor').order_by('-data').first()
        ultima_resposta = Recomendacao.objects.filter(
            talhao=talhao,
            status__in=['emitida', 'aplicada'],
        ).select_related('consultor').order_by('-data').first()
    return render(request, 'consultoria/consultoria_api_agricultor.html', {
        'talhoes': talhoes, 'talhao_selecionado': talhao, 'dados_clima': dados_clima,
        'risco': risco, 'orientacao': orientacao, 'explicacao_resultado': explicacao_resultado, 'possiveis_doencas': possiveis_doencas,
        'analise_pendente': analise_pendente, 'ultima_resposta': ultima_resposta,
    })

@login_required
@perfil_required('agricultor')
def enviar_analise_ao_consultor(request, talhao_pk):
    """Envia o último resultado guardado pelo AgroVision sem repetir a consulta externa."""
    if request.method != 'POST':
        return redirect('consultoria:consultoria_api_agricultor')
    talhao = get_object_or_404(
        Talhao.objects.select_related('propriedade__consultor_responsavel', 'cultura'),
        pk=talhao_pk, propriedade__proprietario=request.user,
    )
    propriedade = talhao.propriedade
    consultor = propriedade.consultor_responsavel
    if not consultor:
        messages.error(request, 'A administração ainda precisa atribuir um consultor a esta propriedade.')
        return redirect('consultoria:consultoria_api_agricultor')
    ultimo_clima = RegistroClima.objects.filter(propriedade=propriedade).order_by('-data').first()
    if not ultimo_clima:
        messages.error(request, 'Faça primeiro a consultoria inteligente do AgroVision para guardar os dados atuais.')
        return redirect('consultoria:consultoria_api_agricultor')
    risco = _risco_talhao(talhao)
    solo = f'Tipo de solo registado: {talhao.tipo_solo}.' if talhao.tipo_solo else 'Sem tipo de solo registado; confirmar com análise laboratorial.'
    clima = (
        f'Dados consultados pelo AgroVision: temperatura {ultimo_clima.temperatura} graus Celsius; '
        f'humidade {ultimo_clima.humidade} por cento; vento {ultimo_clima.vento_velocidade} quilómetros por hora; '
        f'condição {ultimo_clima.descricao}.'
    )
    orientacao = _sugestao_recomendacao_automatica(talhao, risco, dados_solo_extra=solo, dados_clima_extra=clima)
    prefixo = 'Análise AgroVision solicitada pelo agricultor para revisão.\n'
    rascunho = Recomendacao.objects.filter(
        talhao=talhao, consultor=consultor, status='rascunho',
        texto_recomendacao__startswith='Análise AgroVision solicitada',
    ).first() or Recomendacao(talhao=talhao, consultor=consultor, status='rascunho')
    rascunho.dados_solo = solo
    rascunho.dados_clima = clima
    rascunho.texto_recomendacao = prefixo + orientacao
    rascunho.prioridade = risco['prioridade']
    rascunho.save()
    messages.success(request, f'Análise enviada ao consultor {consultor.nome_completo}. Ela ficou como rascunho para revisão e emissão.')
    return redirect(f"{reverse('consultoria:consultoria_api_agricultor')}?talhao={talhao.pk}")


# ==========================================================================
# RECOMENDAÇÕES
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_recomendacoes(request):
    """Lista recomendações conforme o perfil."""
    user = request.user
    recomendacoes = _recomendacoes_visiveis(user)
    busca = request.GET.get('q', '').strip()
    prioridade = request.GET.get('prioridade', '').strip()
    status = request.GET.get('status', '').strip()
    if busca:
        recomendacoes = recomendacoes.filter(
            Q(talhao__nome__icontains=busca) |
            Q(talhao__propriedade__nome__icontains=busca) |
            Q(texto_recomendacao__icontains=busca)
        )
    if prioridade:
        recomendacoes = recomendacoes.filter(prioridade=prioridade)
    if status:
        recomendacoes = recomendacoes.filter(status=status)

    return render(request, 'consultoria/lista_recomendacoes.html', {
        'recomendacoes': recomendacoes,
        'filtros': {'q': busca, 'prioridade': prioridade, 'status': status},
        'prioridades': Recomendacao.PRIORIDADE_CHOICES,
        'status_opcoes': Recomendacao.STATUS_CHOICES,
    })


@login_required
@acesso_tecnico
def nova_recomendacao(request):
    """Cria uma nova recomendação agronómica."""
    if request.method == 'POST':
        talhoes_permitidos = Talhao.objects.filter(propriedade__in=_propriedades_visiveis(request.user))
        talhao = get_object_or_404(talhoes_permitidos, pk=request.POST.get('talhao'))
        risco = _risco_talhao(talhao)
        dados_solo = request.POST.get('dados_solo', '').strip() or (
            f"Tipo de solo registado: {talhao.tipo_solo}." if talhao.tipo_solo else 'Sem análise de solo registada; confirmar com análise laboratorial.'
        )
        ultimo_clima = risco.get('ultimo_clima')
        dados_clima = request.POST.get('dados_clima', '').strip()
        if not dados_clima and ultimo_clima:
            dados_clima = (
                f"Temperatura: {ultimo_clima.temperatura} graus Celsius; humidade: {ultimo_clima.humidade} por cento; "
                f"vento: {ultimo_clima.vento_velocidade} quilómetros por hora; condição: {ultimo_clima.descricao}."
            )
        elif not dados_clima:
            dados_clima = 'Sem registo climático recente; atualizar a meteorologia antes da decisão final.'

        gerar_automaticamente = request.POST.get('gerar_automaticamente') == 'on'
        texto_manual = request.POST.get('texto_recomendacao', '').strip()
        if gerar_automaticamente or not texto_manual:
            texto_recomendacao = _sugestao_recomendacao_automatica(
                talhao, risco, dados_solo_extra=dados_solo, dados_clima_extra=dados_clima
            )
            prioridade = risco['prioridade']
            origem = 'gerada automaticamente pelo AgroVision e guardada para revisão'
        else:
            texto_recomendacao = texto_manual
            prioridade = request.POST.get('prioridade', risco['prioridade'])
            origem = 'criada com o texto revisto pelo técnico'

        rec = Recomendacao(
            talhao=talhao, consultor=request.user, dados_solo=dados_solo, dados_clima=dados_clima,
            texto_recomendacao=texto_recomendacao, prioridade=prioridade,
            status=request.POST.get('status', 'rascunho'),
            foto_evidencia=request.FILES.get('foto_evidencia'),
            foto_resultado=request.FILES.get('foto_resultado'),
        )
        rec.save()
        messages.success(request, f'Recomendação {origem}.')
        return redirect('consultoria:detalhe_recomendacao', pk=rec.pk)

    talhoes = Talhao.objects.filter(propriedade__in=_propriedades_visiveis(request.user))
    talhao_sugerido = None
    risco = None
    sugestao = ''
    talhao_id = request.GET.get('talhao')
    if talhao_id:
        talhao_sugerido = get_object_or_404(talhoes, pk=talhao_id)
    else:
        talhao_sugerido = talhoes.first()

    if talhao_sugerido:
        risco = _risco_talhao(talhao_sugerido)
        sugestao = _sugestao_recomendacao_automatica(talhao_sugerido, risco)

    return render(request, 'consultoria/form_recomendacao.html', {
        'talhoes': talhoes,
        'talhao_sugerido': talhao_sugerido,
        'risco': risco,
        'sugestao': sugestao,
    })


@login_required
@perfil_required('admin', 'consultor')
def responder_recomendacao(request, pk):
    """Permite ao consultor rever a análise e escrever a resposta oficial."""
    recomendacao = get_object_or_404(_recomendacoes_visiveis(request.user), pk=pk)
    if recomendacao.status != 'rascunho':
        messages.info(request, 'A recomendação já foi emitida e não pode ser alterada por este formulário.')
        return redirect('consultoria:detalhe_recomendacao', pk=pk)
    if request.method == 'POST':
        texto = request.POST.get('texto_recomendacao', '').strip()
        if not texto:
            messages.error(request, 'Escreva a resposta técnica antes de guardar.')
        else:
            recomendacao.dados_solo = request.POST.get('dados_solo', '').strip()
            recomendacao.dados_clima = request.POST.get('dados_clima', '').strip()
            recomendacao.texto_recomendacao = texto
            recomendacao.prioridade = request.POST.get('prioridade', recomendacao.prioridade)
            recomendacao.save(update_fields=[
                'dados_solo', 'dados_clima', 'texto_recomendacao', 'prioridade',
            ])
            messages.success(
                request,
                'Resposta guardada. Confira o conteúdo e use Emitir recomendação para enviá-la ao agricultor.',
            )
            return redirect('consultoria:detalhe_recomendacao', pk=pk)
    return render(request, 'consultoria/responder_recomendacao.html', {
        'rec': recomendacao,
        'prioridades': Recomendacao.PRIORIDADE_CHOICES,
    })


@login_required
@perfil_required('admin', 'consultor')
def emitir_recomendacao(request, pk):
    """Publica um rascunho revisto para agricultores e clientes autorizados."""
    recomendacao = get_object_or_404(_recomendacoes_visiveis(request.user), pk=pk)
    if request.method != 'POST':
        messages.error(request, 'Use o botão Emitir recomendação para confirmar a publicação.')
        return redirect('consultoria:detalhe_recomendacao', pk=pk)
    recomendacao.status = 'emitida'
    recomendacao.save(update_fields=['status'])
    messages.success(request, 'Recomendação emitida e disponibilizada aos utilizadores autorizados.')
    return redirect('consultoria:detalhe_recomendacao', pk=pk)


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def detalhe_recomendacao(request, pk):
    """Mostra o detalhe de uma recomendação."""
    recomendacao = get_object_or_404(_recomendacoes_visiveis(request.user), pk=pk)
    return render(request, 'consultoria/detalhe_recomendacao.html', {'rec': recomendacao})


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def exportar_recomendacao_pdf(request, pk):
    """Gera um PDF da recomendação usando Reportlab."""
    rec = _recomendacoes_visiveis(request.user).filter(pk=pk).first()
    if not rec:
        messages.warning(
            request,
            'Esta recomendação ainda não está disponível. Aguarde a revisão e emissão pelo consultor.',
        )
        return redirect('consultoria:lista_recomendacoes')

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('Titulo', parent=styles['Title'], textColor=colors.HexColor('#2E7D32'), fontSize=20, spaceAfter=8)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], textColor=colors.HexColor('#F57C00'), fontSize=12, alignment=TA_CENTER, spaceAfter=20)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=11, leading=16, alignment=TA_JUSTIFY)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1B5E20'), fontName='Helvetica-Bold')

    elementos = []

    # Cabeçalho
    elementos.append(Paragraph("🌱 AgroVision", titulo_style))
    elementos.append(Paragraph("Relatório de Recomendação Agrícola", sub_style))
    elementos.append(Spacer(1, 0.5*cm))

    # Tabela de dados gerais
    dados = [
        ['Data:', rec.data.strftime('%d/%m/%Y %H:%M'), 'Prioridade:', rec.get_prioridade_display()],
        ['Estado:', rec.get_status_display(), 'Consultor:', rec.consultor.nome_completo],
        ['Propriedade:', rec.talhao.propriedade.nome, 'Talhão:', rec.talhao.nome],
        ['Cultura:', str(rec.talhao.cultura or 'N/A'), 'Tipo de solo:', rec.talhao.tipo_solo or 'N/A'],
    ]
    tabela = Table(dados, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    tabela.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2E7D32')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.8*cm))

    # Dados do solo
    if rec.dados_solo:
        elementos.append(Paragraph("📊 Dados do Solo", label_style))
        elementos.append(Spacer(1, 0.2*cm))
        elementos.append(Paragraph(rec.dados_solo.replace('\n', '<br/>'), normal_style))
        elementos.append(Spacer(1, 0.5*cm))

    # Dados do clima
    if rec.dados_clima:
        elementos.append(Paragraph("🌤️ Dados do Clima", label_style))
        elementos.append(Spacer(1, 0.2*cm))
        elementos.append(Paragraph(rec.dados_clima.replace('\n', '<br/>'), normal_style))
        elementos.append(Spacer(1, 0.5*cm))

    # Recomendação técnica
    elementos.append(Paragraph("📝 Recomendação Técnica", label_style))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph(rec.texto_recomendacao.replace('\n', '<br/>'), normal_style))
    elementos.append(Spacer(1, 1*cm))

    # Rodapé
    elementos.append(Spacer(1, 1*cm))
    rodape_style = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elementos.append(Paragraph(
        f"AgroVision — Plataforma de Consultoria Agrícola Inteligente | Documento gerado em {rec.data.strftime('%d/%m/%Y')}",
        rodape_style
    ))

    doc.build(elementos)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recomendacao_{rec.pk}.pdf"'
    return response


# ==========================================================================
# VISITAS TÉCNICAS
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_visitas(request):
    """Lista visitas técnicas conforme o perfil."""
    user = request.user
    visitas = _visitas_visiveis(user)
    busca = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    if busca:
        visitas = visitas.filter(
            Q(propriedade__nome__icontains=busca) |
            Q(responsavel__nome_completo__icontains=busca) |
            Q(observacoes__icontains=busca)
        )
    if tipo:
        visitas = visitas.filter(tipo=tipo)

    return render(request, 'consultoria/lista_visitas.html', {
        'visitas': visitas,
        'filtros': {'q': busca, 'tipo': tipo},
        'tipos_visita': VisitaTecnica.TIPO_CHOICES,
    })


@login_required
@perfil_required('admin', 'tecnico')
def nova_visita(request):
    """Cria uma nova visita técnica com upload de fotos."""
    if request.method == 'POST':
        visita = VisitaTecnica(
            propriedade_id=request.POST.get('propriedade'),
            responsavel=request.user,
            data=request.POST.get('data'),
            tipo=request.POST.get('tipo', 'rotineira'),
            observacoes=request.POST.get('observacoes', ''),
            recomendacao_campo=request.POST.get('recomendacao_campo', ''),
        )
        visita.save()

        # Upload de múltiplas fotos
        fotos = request.FILES.getlist('fotos')
        for foto in fotos:
            FotoVisita.objects.create(visita=visita, imagem=foto)

        messages.success(request, f'Visita técnica registada com sucesso! ({len(fotos)} foto(s) anexada(s))')
        return redirect('consultoria:lista_visitas')

    propriedades = _propriedades_visiveis(request.user)
    return render(request, 'consultoria/form_visita.html', {'propriedades': propriedades})


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def detalhe_visita(request, pk):
    """Detalhe de uma visita técnica com as fotos."""
    visita = get_object_or_404(_visitas_visiveis(request.user), pk=pk)
    fotos = visita.fotos.all()
    return render(request, 'consultoria/detalhe_visita.html', {'visita': visita, 'fotos': fotos})


# ==========================================================================
# PRAGAS E DOENÇAS
# ==========================================================================
@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_pragas(request):
    """Lista pragas e doenças registadas."""
    user = request.user
    pragas = PragaDoenca.objects.filter(talhao__propriedade__in=_propriedades_visiveis(user))
    busca = request.GET.get('q', '').strip()
    severidade = request.GET.get('severidade', '').strip()
    estado = request.GET.get('estado', '').strip()
    if busca:
        pragas = pragas.filter(
            Q(nome__icontains=busca) |
            Q(talhao__nome__icontains=busca) |
            Q(talhao__propriedade__nome__icontains=busca)
        )
    if severidade:
        pragas = pragas.filter(severidade=severidade)
    if estado == 'ativo':
        pragas = pragas.filter(resolvido=False)
    elif estado == 'resolvido':
        pragas = pragas.filter(resolvido=True)

    return render(request, 'consultoria/lista_pragas.html', {
        'pragas': pragas,
        'filtros': {'q': busca, 'severidade': severidade, 'estado': estado},
        'severidades': PragaDoenca.SEVERIDADE_CHOICES,
    })


@login_required
@perfil_required('admin', 'tecnico')
def nova_praga(request):
    """Regista uma nova praga/doença."""
    if request.method == 'POST':
        from datetime import date as date_cls
        praga = PragaDoenca.objects.create(
            talhao_id=request.POST.get('talhao'),
            nome=request.POST.get('nome', ''),
            severidade=request.POST.get('severidade', 'baixa'),
            data_deteccao=request.POST.get('data_deteccao') or date_cls.today(),
            tratamento_sugerido=request.POST.get('tratamento_sugerido', ''),
            foto_diagnostico=request.FILES.get('foto_diagnostico'),
            foto_resultado=request.FILES.get('foto_resultado'),
        )
        if praga.severidade in ['alta', 'critica']:
            Alerta.objects.get_or_create(
                propriedade=praga.talhao.propriedade,
                tipo='praga',
                lido=False,
                defaults={
                    'severidade': 'urgente' if praga.severidade == 'critica' else 'aviso',
                    'mensagem': (
                        f"Praga/doença registada no talhão {praga.talhao.nome}: "
                        f"{praga.nome} ({praga.get_severidade_display()})."
                    ),
                },
            )
        messages.success(request, 'Praga/Doença registada com sucesso!')
        return redirect('consultoria:lista_pragas')

    talhoes = Talhao.objects.filter(propriedade__in=_propriedades_visiveis(request.user))
    return render(request, 'consultoria/form_praga.html', {'talhoes': talhoes})
