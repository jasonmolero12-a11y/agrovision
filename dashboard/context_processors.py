"""Contexto global para notificações do painel."""

from contas.models import MensagemSuporte, Utilizador
from meteorologia.models import Alerta
from propriedades.models import Propriedade


def notificacoes_sistema(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    pedidos_pendentes = 0
    mensagens_suporte_pendentes = 0
    respostas_suporte_nao_lidas = 0
    alertas_qs = Alerta.objects.none()

    if user.is_admin or user.is_superuser:
        pedidos_pendentes = Utilizador.objects.filter(status_solicitacao='pendente').count()
        mensagens_suporte_pendentes = MensagemSuporte.objects.filter(status__in=['aberta', 'em_analise']).count()
        alertas_qs = Alerta.objects.filter(lido=False)
    else:
        respostas_suporte_nao_lidas = MensagemSuporte.objects.filter(utilizador=user, resposta_admin__gt='', resposta_lida=False).count()
        if user.is_consultor:
            propriedades = Propriedade.objects.filter(consultor_responsavel=user)
        elif user.is_agricultor or user.is_cliente:
            propriedades = Propriedade.objects.filter(proprietario=user)
        elif user.is_tecnico or user.is_analista:
            propriedades = Propriedade.objects.all()
        else:
            propriedades = Propriedade.objects.none()
        alertas_qs = Alerta.objects.filter(propriedade__in=propriedades, lido=False)

    return {
        'notificacoes_pedidos_pendentes': pedidos_pendentes,
        'notificacoes_alertas_pendentes': alertas_qs.count(),
        'notificacoes_alertas_recentes': alertas_qs.order_by('-data')[:3],
        'notificacoes_mensagens_suporte': mensagens_suporte_pendentes,
        'notificacoes_respostas_suporte': respostas_suporte_nao_lidas,
        'notificacoes_total': pedidos_pendentes + alertas_qs.count() + mensagens_suporte_pendentes + respostas_suporte_nao_lidas,
    }
