"""URLs da app publico - portal institucional."""

from django.urls import path
from . import views

app_name = 'publico'

urlpatterns = [
    path('', views.home_publico, name='home'),
    path('servicos/', views.servicos, name='servicos'),
    path('sobre/', views.sobre, name='sobre'),
    path('contacto/', views.contacto, name='contacto'),
]
