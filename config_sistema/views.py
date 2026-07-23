"""
Views da app config_sistema - Configuração da API meteorológica.

Painel onde o Administrador insere a chave da API e escolhe o provedor.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from contas.decorators import admin_required
from .models import ConfiguracaoAPI


@login_required
@admin_required
def configurar_api(request):
    """Painel para o Admin configurar a API meteorológica."""
    config = ConfiguracaoAPI.carregar()

    if request.method == 'POST':
        config.provedor = request.POST.get('provedor', 'openweather')
        config.api_key = request.POST.get('api_key', '')
        config.url_base = request.POST.get('url_base', '')
        config.cidade_padrao = request.POST.get('cidade_padrao', 'Luanda')
        config.ativo = request.POST.get('ativo') == 'on'
        config.ia_provedor = request.POST.get('ia_provedor', 'gemini')
        config.ia_api_key = request.POST.get('ia_api_key', '')
        config.ia_modelo = request.POST.get('ia_modelo', 'gemini-1.5-flash')
        config.ia_url_base = request.POST.get('ia_url_base', '')
        config.ia_ativo = request.POST.get('ia_ativo') == 'on'
        config.validar_nome_seguro = request.POST.get('validar_nome_seguro') == 'on'
        config.login_exigir_identificador_valido = request.POST.get('login_exigir_identificador_valido') == 'on'
        config.login_exigir_senha_alfanumerica = request.POST.get('login_exigir_senha_alfanumerica') == 'on'
        config.cadastro_senha_exigir_letra = request.POST.get('cadastro_senha_exigir_letra') == 'on'
        config.cadastro_senha_exigir_numero = request.POST.get('cadastro_senha_exigir_numero') == 'on'
        config.permitir_login_por_nome = request.POST.get('permitir_login_por_nome') == 'on'
        config.save()
        messages.success(request, 'Configuração da API guardada com sucesso!')
        return redirect('config_sistema:config_api')

    return render(request, 'config_sistema/config_api.html', {'config': config})


@login_required
@admin_required
def testar_api(request):
    """Testa a ligação à API meteorológica (AJAX)."""
    from meteorologia.views import obter_previsao_api

    resultado = obter_previsao_api()
    if resultado is None:
        return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível obter dados da API.'})

    if 'erro' in resultado:
        return JsonResponse({'sucesso': False, 'mensagem': resultado['erro']})

    return JsonResponse({
        'sucesso': True,
        'mensagem': f"API a funcionar! Cidade: {resultado.get('cidade')} | Temp: {resultado.get('temperatura')}°C",
        'dados': resultado,
    })
