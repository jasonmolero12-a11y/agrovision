"""
Views da app contas - Autenticação e gestão de utilizadores.

Inclui:
  - Login (por email ou nome)
  - Logout
  - Registo de novos utilizadores
  - Perfil do utilizador
  - Gestão de utilizadores (Admin)
"""

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import MensagemSuporte, Utilizador
from .forms import (FormEditarPerfil, FormLogin, FormMensagemSuporte, FormRegisto, FormRespostaSuporte, FormSolicitarPerfil)


def login_view(request):
    """View de login - autentica por email ou nome e redireciona conforme o perfil."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = FormLogin(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.nome_completo or user.email}!')
            # Redireciona para 'next' se existir, senão para o dashboard
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'dashboard:home')
    else:
        form = FormLogin()

    return render(request, 'contas/login.html', {'form': form})


def logout_view(request):
    """View de logout."""
    logout(request)
    messages.info(request, 'Sessão terminada com sucesso.')
    return redirect('publico:home')


def registo_view(request):
    """View de registo de novo utilizador."""
    if request.method == 'POST':
        form = FormRegisto(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.nome_completo = form.cleaned_data['nome_completo']
            user.telefone = form.cleaned_data.get('telefone', '')
            # O registo publico cria visitante. O perfil definitivo depende da aprovacao do admin.
            user.tipo_utilizador = 'visitante'
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo à AgroVision.')
            return redirect('dashboard:home')
    else:
        form = FormRegisto()

    return render(request, 'contas/registo.html', {'form': form})


@login_required
def perfil_view(request):
    """View do perfil do utilizador logado."""
    if request.method == 'POST':
        form = FormEditarPerfil(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('contas:perfil')
    else:
        form = FormEditarPerfil(instance=request.user)

    return render(request, 'contas/perfil.html', {'form': form})


@login_required
def solicitar_perfil_view(request):
    """Permite ao visitante solicitar agricultor, consultor, analista ou tecnico."""
    if request.method == 'POST':
        form = FormSolicitarPerfil(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.status_solicitacao = 'pendente'
            user.data_solicitacao = timezone.now()
            user.save()
            messages.success(request, 'Solicitação enviada com sucesso. A administração responderá no prazo máximo de 48 horas.')
            return redirect('contas:solicitar_perfil')
    else:
        form = FormSolicitarPerfil(instance=request.user)

    return render(request, 'contas/solicitar_perfil.html', {
        'form': form,
        'pedido_pendente': request.user.status_solicitacao == 'pendente',
        'prazo_expirado': request.user.prazo_solicitacao_expirado,
    })


@login_required
def listar_utilizadores_view(request):
    """Lista todos os utilizadores (apenas Admin)."""
    if not (request.user.is_admin or request.user.is_superuser):
        messages.error(request, 'Não tem permissão para aceder a esta página.')
        return redirect('dashboard:home')

    utilizadores = Utilizador.objects.all().order_by('nome_completo')
    busca = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    status = request.GET.get('status', '').strip()
    if busca:
        utilizadores = utilizadores.filter(
            Q(nome_completo__icontains=busca) |
            Q(email__icontains=busca) |
            Q(telefone__icontains=busca)
        )
    if tipo:
        utilizadores = utilizadores.filter(tipo_utilizador=tipo)
    if status:
        utilizadores = utilizadores.filter(status_solicitacao=status)
    # Estatísticas rápidas
    stats = {
        'total': utilizadores.count(),
        'admins': utilizadores.filter(tipo_utilizador='admin').count(),
        'consultores': utilizadores.filter(tipo_utilizador='consultor').count(),
        'analistas': utilizadores.filter(tipo_utilizador='analista').count(),
        'tecnicos': utilizadores.filter(tipo_utilizador='tecnico').count(),
        'agricultores': utilizadores.filter(tipo_utilizador='agricultor').count(),
        'clientes': utilizadores.filter(tipo_utilizador='cliente').count(),
    }
    return render(request, 'contas/lista_utilizadores.html', {
        'utilizadores': utilizadores,
        'stats': stats,
        'filtros': {'q': busca, 'tipo': tipo, 'status': status},
        'tipos': Utilizador.TIPO_CHOICES,
        'status_opcoes': Utilizador.STATUS_SOLICITACAO_CHOICES,
    })


@login_required
def mensagens_suporte_view(request):
    is_admin = request.user.is_admin or request.user.is_superuser
    mensagens_qs = MensagemSuporte.objects.select_related('utilizador', 'respondido_por').all() if is_admin else MensagemSuporte.objects.filter(utilizador=request.user)
    status = request.GET.get('status', '').strip()
    if status:
        mensagens_qs = mensagens_qs.filter(status=status)
    return render(request, 'contas/mensagens_suporte.html', {
        'mensagens_suporte': mensagens_qs, 'is_admin_suporte': is_admin,
        'status_atual': status, 'status_opcoes': MensagemSuporte.STATUS_CHOICES,
    })


@login_required
def nova_mensagem_suporte_view(request):
    if request.user.is_admin or request.user.is_superuser:
        messages.info(request, 'Administradores respondem às mensagens recebidas na caixa de atendimento.')
        return redirect('contas:mensagens_suporte')
    if request.method == 'POST':
        form = FormMensagemSuporte(request.POST)
        if form.is_valid():
            atendimento = form.save(commit=False)
            atendimento.utilizador = request.user
            atendimento.save()
            messages.success(request, 'Mensagem enviada. A administração foi notificada.')
            return redirect('contas:detalhe_mensagem_suporte', pk=atendimento.pk)
    else:
        initial = {'categoria': 'solicitacao' if request.user.is_visitante else 'outro'}
        propriedade_id = request.GET.get('propriedade')
        if request.user.is_cliente and propriedade_id:
            from propriedades.models import Propriedade
            propriedade = Propriedade.objects.filter(pk=propriedade_id, exposta_para_clientes=True).first()
            if propriedade:
                initial.update({'categoria': 'solicitacao', 'assunto': f'Interesse comercial em {propriedade.nome}', 'mensagem': f'Gostaria de receber informações para comprar produtos da propriedade {propriedade.nome}.'})
        form = FormMensagemSuporte(initial=initial)
    return render(request, 'contas/nova_mensagem_suporte.html', {'form': form})


@login_required
def detalhe_mensagem_suporte_view(request, pk):
    is_admin = request.user.is_admin or request.user.is_superuser
    atendimento = get_object_or_404(MensagemSuporte.objects.select_related('utilizador', 'respondido_por'), pk=pk)
    if not is_admin and atendimento.utilizador_id != request.user.pk:
        messages.error(request, 'Não tem permissão para consultar esta mensagem.')
        return redirect('contas:mensagens_suporte')
    if not is_admin and atendimento.resposta_admin and not atendimento.resposta_lida:
        atendimento.resposta_lida = True
        atendimento.save(update_fields=['resposta_lida'])
    form_resposta = None
    if is_admin:
        if request.method == 'POST':
            form_resposta = FormRespostaSuporte(request.POST, instance=atendimento)
            if form_resposta.is_valid():
                atendimento = form_resposta.save(commit=False)
                if atendimento.resposta_admin.strip():
                    atendimento.respondido_por = request.user
                    atendimento.respondida_em = timezone.now()
                    atendimento.resposta_lida = False
                    if atendimento.status in ('aberta', 'em_analise'):
                        atendimento.status = 'respondida'
                atendimento.save()
                messages.success(request, 'Resposta enviada ao utilizador.')
                return redirect('contas:detalhe_mensagem_suporte', pk=atendimento.pk)
        else:
            form_resposta = FormRespostaSuporte(instance=atendimento)
    return render(request, 'contas/detalhe_mensagem_suporte.html', {'atendimento': atendimento, 'form_resposta': form_resposta, 'is_admin_suporte': is_admin})
