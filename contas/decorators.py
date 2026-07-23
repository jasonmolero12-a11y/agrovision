"""
Decorators de permissão da AgroVision.

Controlam o acesso às views conforme o tipo de utilizador:
  - admin_required      → só Administrador
  - consultor_required  → só Consultor Agrícola
  - analista_required   → só Analista de Dados
  - tecnico_required    → só Técnico de Campo
  - agricultor_required → só Agricultor
  - acesso_tecnico      → Administrador ou Consultor
  - acesso_operacional  → Técnico ou Agricultor
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def perfil_required(*tipos_permitidos):
    """
    Decorator genérico que verifica se o utilizador tem um dos tipos permitidos.
    Ex: @perfil_required('admin', 'consultor')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            # Superuser tem sempre acesso
            if request.user.is_superuser or request.user.tipo_utilizador in tipos_permitidos:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Não tem permissão para aceder a esta página.')
            return redirect('dashboard:home')
        return _wrapped
    return decorator


# Decorators específicos por perfil
def admin_required(view_func):
    """Restringe o acesso ao Administrador."""
    return perfil_required('admin')(view_func)


def consultor_required(view_func):
    """Restringe o acesso ao Consultor Agrícola."""
    return perfil_required('consultor')(view_func)


def analista_required(view_func):
    """Restringe o acesso ao Analista de Dados."""
    return perfil_required('analista')(view_func)


def tecnico_required(view_func):
    """Restringe o acesso ao Técnico de Campo."""
    return perfil_required('tecnico')(view_func)


def agricultor_required(view_func):
    """Restringe o acesso ao Agricultor."""
    return perfil_required('agricultor')(view_func)


def acesso_tecnico(view_func):
    """Restringe o acesso a perfis técnicos (Admin, Consultor, Analista)."""
    return perfil_required('admin', 'consultor')(view_func)


def acesso_operacional(view_func):
    """Restringe o acesso a perfis operacionais (Técnico, Agricultor)."""
    return perfil_required('tecnico', 'agricultor')(view_func)
