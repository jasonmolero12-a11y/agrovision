"""Barreira central para perfis ainda não aprovados."""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import Resolver404, resolve


class RestringirVisitanteMiddleware:
    """Impede que visitantes contornem o menu digitando URLs operacionais."""

    ROTAS_PERMITIDAS = {
        'dashboard:home', 'dashboard:chatbot',
        'contas:perfil', 'contas:solicitar_perfil', 'contas:logout',
        'contas:mensagens_suporte', 'contas:nova_mensagem_suporte',
        'contas:detalhe_mensagem_suporte',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'is_visitante', False):
            try:
                match = resolve(request.path_info)
            except Resolver404:
                return self.get_response(request)
            rota = f'{match.namespace}:{match.url_name}' if match.namespace else match.url_name
            if match.namespace not in ('publico',) and rota not in self.ROTAS_PERMITIDAS:
                messages.warning(request, 'O seu perfil ainda não permite acesso a esta área. Solicite a validação do perfil.')
                return redirect('contas:solicitar_perfil')
        return self.get_response(request)
