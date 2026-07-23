"""
ASGI config for agrovision project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from agrovision.django_compat import aplicar_patch_contexto
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrovision.settings')
aplicar_patch_contexto()

application = get_asgi_application()
