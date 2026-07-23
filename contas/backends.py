from django.contrib.auth.backends import ModelBackend
import re

from .models import Utilizador


class EmailOuNomeBackend(ModelBackend):
    """Autentica por email ou por nome completo unico."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identificador = (username or kwargs.get('email') or '').strip()
        if not identificador or not password:
            return None
        try:
            from config_sistema.models import ConfiguracaoAPI
            config = ConfiguracaoAPI.carregar()
        except Exception:
            config = None
        if (not config or config.login_exigir_identificador_valido) and not re.search(r'[^\W_]', identificador, flags=re.UNICODE):
            return None
        if (not config or config.login_exigir_senha_alfanumerica) and not re.search(r'[^\W_]', password, flags=re.UNICODE):
            return None
        if config and not config.permitir_login_por_nome and '@' not in identificador:
            return None

        if '@' in identificador:
            utilizadores = Utilizador.objects.filter(email__iexact=identificador)
        else:
            utilizadores = Utilizador.objects.filter(nome_completo__iexact=identificador)

        if utilizadores.count() != 1:
            return None

        user = utilizadores.first()
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
