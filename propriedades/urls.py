"""URLs da app propriedades."""

from django.urls import path
from . import views

app_name = 'propriedades'

urlpatterns = [
    path('', views.lista_propriedades, name='lista'),
    path('mercado/', views.mercado_agricola, name='mercado'),
    path('mercado/pedidos/', views.pedidos_compra, name='pedidos_compra'),
    path('mercado/pedidos/<int:pk>/responder/', views.responder_pedido_compra, name='responder_pedido_compra'),
    path('mercado/comparar/', views.comparar_mercado, name='mercado_comparar'),
    path('mercado/<int:pk>/favoritar/', views.favoritar_mercado, name='mercado_favoritar'),
    path('mercado/<int:pk>/', views.detalhe_mercado, name='mercado_detalhe'),
    path('mercado/<int:pk>/comprar/', views.solicitar_compra, name='mercado_comprar'),
    path('nova/', views.nova_propriedade, name='nova'),
    path('<int:pk>/detalhe/', views.detalhe_propriedade, name='detalhe'),
    path('<int:propriedade_pk>/producao/nova/', views.novo_registo_producao, name='nova_producao'),
    path('<int:pk>/editar/', views.editar_propriedade, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_propriedade, name='eliminar'),
    path('talhoes/', views.lista_talhoes, name='lista_talhoes'),
    path('talhoes/novo/', views.novo_talhao, name='novo_talhao'),
    path('talhoes/<int:pk>/editar/', views.editar_talhao, name='editar_talhao'),
    path('culturas/', views.lista_culturas, name='lista_culturas'),
    path('culturas/nova/', views.nova_cultura, name='nova_cultura'),
]
