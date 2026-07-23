"""URLs da app config_sistema."""

from django.urls import path
from . import views

app_name = 'config_sistema'

urlpatterns = [
    path('config-api/', views.configurar_api, name='config_api'),
    path('testar-api/', views.testar_api, name='testar_api'),
]
