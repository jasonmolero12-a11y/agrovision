"""URLs da app dashboard."""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('chatbot/', views.chatbot_responder, name='chatbot'),
]
