"""
Views da app publico - Portal institucional (sem login).

Acesso a Visitantes Públicos: informações gerais, serviços e contacto.
"""

from django.shortcuts import render


def home_publico(request):
    """Página inicial do portal público da AgroVision."""
    return render(request, 'publico/home.html')


def servicos(request):
    """Página de serviços oferecidos pela AgroVision."""
    return render(request, 'publico/servicos.html')


def sobre(request):
    """Página sobre a AgroVision."""
    return render(request, 'publico/sobre.html')


def contacto(request):
    """Página de contacto."""
    return render(request, 'publico/contacto.html')
