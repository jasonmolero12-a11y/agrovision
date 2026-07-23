"""URLs da app meteorologia."""

from django.urls import path
from . import views

app_name = 'meteorologia'

urlpatterns = [
    path('previsao/', views.previsao_meteorologica, name='previsao'),
    path('alertas/', views.lista_alertas, name='lista_alertas'),
    path('alertas/<int:pk>/marcar-lido/', views.marcar_alerta_lido, name='marcar_alerta_lido'),
    path('registros/', views.lista_registros, name='lista_registros'),
]
