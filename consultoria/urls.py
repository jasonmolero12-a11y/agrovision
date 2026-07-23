"""URLs da app consultoria."""

from django.urls import path
from . import views

app_name = 'consultoria'

urlpatterns = [
    path('agricultor/api/', views.consultoria_api_agricultor, name='consultoria_api_agricultor'),
    path('agricultor/analise/<int:talhao_pk>/enviar/', views.enviar_analise_ao_consultor, name='enviar_analise_consultor'),
    path('recomendacoes/', views.lista_recomendacoes, name='lista_recomendacoes'),
    path('recomendacoes/nova/', views.nova_recomendacao, name='nova_recomendacao'),
    path('recomendacoes/<int:pk>/responder/', views.responder_recomendacao, name='responder_recomendacao'),
    path('recomendacoes/<int:pk>/detalhe/', views.detalhe_recomendacao, name='detalhe_recomendacao'),
    path('recomendacoes/<int:pk>/emitir/', views.emitir_recomendacao, name='emitir_recomendacao'),
    path('recomendacoes/<int:pk>/pdf/', views.exportar_recomendacao_pdf, name='pdf_recomendacao'),
    path('visitas/', views.lista_visitas, name='lista_visitas'),
    path('visitas/nova/', views.nova_visita, name='nova_visita'),
    path('visitas/<int:pk>/detalhe/', views.detalhe_visita, name='detalhe_visita'),
    path('pragas/', views.lista_pragas, name='lista_pragas'),
    path('pragas/nova/', views.nova_praga, name='nova_praga'),
]
