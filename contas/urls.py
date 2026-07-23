"""URLs da app contas - autenticação e gestão de utilizadores."""

from django.urls import path
from . import views

app_name = 'contas'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registo/', views.registo_view, name='registo'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('solicitar-perfil/', views.solicitar_perfil_view, name='solicitar_perfil'),
    path('atendimento/', views.mensagens_suporte_view, name='mensagens_suporte'),
    path('atendimento/nova/', views.nova_mensagem_suporte_view, name='nova_mensagem_suporte'),
    path('atendimento/<int:pk>/', views.detalhe_mensagem_suporte_view, name='detalhe_mensagem_suporte'),
    path('utilizadores/', views.listar_utilizadores_view, name='lista_utilizadores'),
]
