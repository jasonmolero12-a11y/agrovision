"""
URL configuration principal do projeto AgroVision.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Portal público (raiz do site)
    path('', include('publico.urls')),

    # Autenticação
    path('', include('contas.urls')),

    # Dashboard
    path('dashboard/', include('dashboard.urls')),

    # Apps de domínio
    path('propriedades/', include('propriedades.urls')),
    path('consultoria/', include('consultoria.urls')),
    path('meteorologia/', include('meteorologia.urls')),

    # Configuração do sistema (Admin)
    path('config/', include('config_sistema.urls')),
]

# Servir ficheiros media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
