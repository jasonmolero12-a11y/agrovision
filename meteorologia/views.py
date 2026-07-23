"""
Views da app meteorologia - Previsão, Alertas e Registros de Clima.

A previsão é obtida via API externa configurada no painel admin
(OpenWeatherMap ou Open-Meteo).
"""

import requests
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from contas.decorators import perfil_required
from config_sistema.models import ConfiguracaoAPI
from config_sistema.ia import gerar_texto_ia
from propriedades.models import Propriedade
from .models import RegistroClima, Alerta


LOCALIDADES_AGRICOLAS_ANGOLA = [
    'Luanda', 'Icolo e Bengo', 'Cacuaco', 'Viana',
    'Bengo', 'Dande', 'Ambriz', 'Nambuangongo',
    'Benguela', 'Lobito', 'Catumbela', 'Ganda', 'Cubal',
    'Huambo', 'Caala', 'Bailundo', 'Longonjo',
    'Huíla', 'Lubango', 'Chibia', 'Caconda', 'Matala',
    'Cuanza Sul', 'Sumbe', 'Cela', 'Quibala', 'Waku-Kungo',
    'Malanje', 'Cacuso', 'Calandula', 'Kiwaba Nzoji',
    'Bié', 'Kuito', 'Camacupa', 'Andulo',
    'Uíge', 'Negage', 'Damba', 'Sanza Pombo',
    'Zaire', 'Mbanza Kongo', 'Soyo',
    'Namibe', 'Moçâmedes', 'Tômbwa',
]

DESCRICOES_WMO = {0: 'Céu limpo', 1: 'Predominantemente limpo', 2: 'Parcialmente nublado', 3: 'Encoberto', 45: 'Nevoeiro', 48: 'Nevoeiro com geada', 51: 'Chuvisco fraco', 53: 'Chuvisco moderado', 55: 'Chuvisco intenso', 56: 'Chuvisco gelado fraco', 57: 'Chuvisco gelado intenso', 61: 'Chuva fraca', 63: 'Chuva moderada', 65: 'Chuva forte', 66: 'Chuva gelada fraca', 67: 'Chuva gelada forte', 71: 'Neve fraca', 73: 'Neve moderada', 75: 'Neve forte', 77: 'Grãos de neve', 80: 'Aguaceiros fracos', 81: 'Aguaceiros moderados', 82: 'Aguaceiros fortes', 85: 'Aguaceiros de neve fracos', 86: 'Aguaceiros de neve fortes', 95: 'Trovoada', 96: 'Trovoada com granizo fraco', 99: 'Trovoada com granizo forte'}

def _descricao_codigo_tempo(codigo):
    try:
        return DESCRICOES_WMO.get(int(codigo), 'Condição meteorológica não classificada')
    except (TypeError, ValueError):
        return 'Condição meteorológica indisponível'

def _analise_agricola_local(dados):
    temperatura, humidade, vento = dados.get('temperatura'), dados.get('humidade'), dados.get('vento')
    precipitacao = dados.get('precipitacao') or 0
    resumo = dados.get('resumo_7_dias', {})
    chuva_7d, temp_max = resumo.get('chuva_total'), resumo.get('temperatura_maxima')
    observacoes = []
    if temperatura is not None and float(temperatura) >= 35:
        observacoes.append('Há risco de stress térmico; priorize rega nas horas frescas e proteja mudas jovens.')
    elif temperatura is not None and 20 <= float(temperatura) < 35:
        observacoes.append('A temperatura atual é compatível com várias culturas tropicais, desde que solo e água sejam adequados.')
    elif temperatura is not None:
        observacoes.append('A temperatura está baixa para algumas culturas tropicais; acompanhe mudas e culturas sensíveis.')
    if humidade is not None and float(humidade) >= 85:
        observacoes.append('A humidade elevada favorece doenças fúngicas; aumente a vigilância nas folhas e a ventilação da cultura.')
    if vento is not None and float(vento) >= 25:
        observacoes.append('Evite pulverização enquanto o vento estiver forte, devido ao risco de deriva.')
    if float(precipitacao) > 5:
        observacoes.append('Há precipitação relevante agora; verifique a drenagem e adie a rega.')
    elif chuva_7d is not None and float(chuva_7d) < 5:
        observacoes.append('A previsão de sete dias indica pouca chuva; confirme a disponibilidade de irrigação.')
    elif chuva_7d is not None and float(chuva_7d) >= 35:
        observacoes.append('A chuva acumulada prevista exige atenção à drenagem, erosão e operações com máquinas.')
    referencia = temp_max if temp_max is not None else temperatura
    culturas = []
    if referencia is not None:
        referencia = float(referencia)
        culturas = ['mandioca', 'milho', 'feijão', 'batata-doce'] if referencia >= 27 else (['milho', 'feijão', 'hortaliças', 'batata'] if referencia >= 20 else ['batata', 'hortaliças de clima ameno'])
    return {'texto': ' '.join(observacoes) or 'Não há dados suficientes para produzir uma observação agrícola.', 'culturas': culturas, 'aviso': 'Sugestão preliminar baseada no clima. A escolha da cultura também exige análise do solo, época agrícola, água disponível, altitude, pragas e mercado.', 'motor': 'Motor agronómico explicável'}

def _enriquecer_com_analise(dados):
    analise = _analise_agricola_local(dados)
    contexto = f"Local: {dados.get('cidade')}; condição: {dados.get('descricao')}; temperatura: {dados.get('temperatura')} °C; humidade: {dados.get('humidade')}%; vento: {dados.get('vento')} km/h; precipitação: {dados.get('precipitacao')} mm; previsão de 7 dias: {dados.get('resumo_7_dias', {})}. Análise local: {analise['texto']}"
    texto_ia = gerar_texto_ia('Explique em até 120 palavras a condição meteorológica e dê uma observação agrícola prudente. Não afirme que uma cultura é adequada apenas pelo clima; mencione as limitações.', contexto=contexto, timeout=20)
    if texto_ia:
        analise['texto'], analise['motor'] = texto_ia, 'Assistente IA com dados meteorológicos reais'
    dados['analise_agricola'] = analise
    return dados



def _propriedades_visiveis(user):
    if user.is_admin or user.is_superuser or user.is_analista or user.is_tecnico:
        return Propriedade.objects.all()
    if user.is_consultor:
        return Propriedade.objects.filter(consultor_responsavel=user)
    if user.is_agricultor:
        return Propriedade.objects.filter(proprietario=user)
    if user.is_cliente:
        return Propriedade.objects.filter(clientes_autorizados=user)
    return Propriedade.objects.none()


def _guardar_registo_e_alerta(propriedade, dados_clima):
    if not propriedade or not dados_clima or dados_clima.get('erro'):
        return

    temperatura = dados_clima.get('temperatura')
    vento = dados_clima.get('vento')

    RegistroClima.objects.create(
        propriedade=propriedade,
        temperatura=temperatura,
        humidade=dados_clima.get('humidade'),
        vento_velocidade=vento,
        descricao=dados_clima.get('descricao', ''),
    )

    if temperatura is not None and float(temperatura) >= 35:
        Alerta.objects.get_or_create(
            propriedade=propriedade,
            tipo='calor_extremo',
            lido=False,
            defaults={
                'severidade': 'urgente',
                'mensagem': f"Temperatura elevada ({temperatura} C). Reforcar monitoramento e irrigacao.",
            },
        )

    if vento is not None and float(vento) >= 40:
        Alerta.objects.get_or_create(
            propriedade=propriedade,
            tipo='vento_forte',
            lido=False,
            defaults={
                'severidade': 'aviso',
                'mensagem': f"Vento forte detectado ({vento} km/h). Verificar culturas sensiveis e estruturas.",
            },
        )


def obter_previsao_api(cidade=None):
    """
    Faz a chamada à API meteorológica configurada no painel admin.

    Retorna um dicionário com os dados do clima ou None se houver erro.
    """
    config = ConfiguracaoAPI.carregar()
    cidade = cidade or config.cidade_padrao or 'Luanda'

    try:
        if config.provedor == 'openweather' and config.api_key:
            # ===== OpenWeatherMap =====
            url_base = config.url_base or 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': cidade,
                'appid': config.api_key,
                'units': 'metric',
                'lang': 'pt_pt'
            }
            response = requests.get(url_base, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                'provedor': 'OpenWeatherMap',
                'cidade': data.get('name', cidade),
                'temperatura': data.get('main', {}).get('temp'),
                'humidade': data.get('main', {}).get('humidity'),
                'vento': data.get('wind', {}).get('speed'),
                'descricao': data.get('weather', [{}])[0].get('description', ''),
                'icone': data.get('weather', [{}])[0].get('icon', ''),
                'consultado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
            }

        else:
            # ===== Open-Meteo (gratuito, sem chave) =====
            # Primeiro: obter coordenadas da cidade
            geo_url = 'https://geocoding-api.open-meteo.com/v1/search'
            geo_response = requests.get(geo_url, params={'name': cidade, 'count': 1, 'language': 'pt'}, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if not geo_data.get('results'):
                return None

            local_geo = geo_data['results'][0]
            lat = local_geo['latitude']
            lon = local_geo['longitude']
            nome_cidade = local_geo['name']
            provincia = local_geo.get('admin1') or local_geo.get('admin2') or ''

            # Segundo: obter o clima. O admin pode preencher a base:
            # https://api.open-meteo.com/v1
            url_base = (config.url_base or 'https://api.open-meteo.com/v1').rstrip('/')
            clima_url = url_base if url_base.endswith('/forecast') else f'{url_base}/forecast'
            clima_response = requests.get(clima_url, params={
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max',
                'forecast_days': 7,
                'timezone': 'auto',
            }, timeout=10)
            clima_response.raise_for_status()
            clima_data = clima_response.json()

            cw = clima_data.get('current', {})
            daily = clima_data.get('daily', {})
            chuva_diaria = daily.get('precipitation_sum') or []
            maximas = daily.get('temperature_2m_max') or []
            minimas = daily.get('temperature_2m_min') or []
            probabilidades = daily.get('precipitation_probability_max') or []
            dias = []
            for indice, data_dia in enumerate(daily.get('time') or []):
                dias.append({'data': data_dia, 'maxima': maximas[indice] if indice < len(maximas) else None, 'minima': minimas[indice] if indice < len(minimas) else None, 'chuva': chuva_diaria[indice] if indice < len(chuva_diaria) else None, 'probabilidade': probabilidades[indice] if indice < len(probabilidades) else None})
            resultado = {
                'provedor': 'Open-Meteo', 'cidade': nome_cidade, 'provincia': provincia, 'latitude': lat, 'longitude': lon,
                'temperatura': cw.get('temperature_2m'), 'humidade': cw.get('relative_humidity_2m'),
                'vento': cw.get('wind_speed_10m'), 'precipitacao': cw.get('precipitation'),
                'codigo_tempo': cw.get('weather_code'), 'descricao': _descricao_codigo_tempo(cw.get('weather_code')), 'icone': '',
                'consultado_em': cw.get('time') or datetime.now().strftime('%d/%m/%Y %H:%M'), 'previsao_7_dias': dias,
                'resumo_7_dias': {'chuva_total': round(sum(v or 0 for v in chuva_diaria), 1), 'temperatura_maxima': max(maximas) if maximas else None, 'temperatura_minima': min(minimas) if minimas else None, 'probabilidade_maxima_chuva': max(probabilidades) if probabilidades else None},
                'fonte_url': 'https://open-meteo.com/',
            }
            return _enriquecer_com_analise(resultado)


    except requests.exceptions.Timeout:
        return {'erro': 'Tempo limite excedido ao contactar a API.'}
    except requests.exceptions.ConnectionError:
        return {'erro': 'Não foi possível ligar à API. Verifique a internet.'}
    except requests.exceptions.HTTPError as e:
        return {'erro': f'Erro da API: {e.response.status_code}'}
    except Exception as e:
        return {'erro': f'Erro inesperado: {str(e)}'}


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def previsao_meteorologica(request):
    """Mostra a previsão meteorológica atual."""
    config = ConfiguracaoAPI.carregar()

    # Se o utilizador escolheu outra cidade para pesquisar
    cidade = request.GET.get('cidade', '')

    dados_clima = obter_previsao_api(cidade) if cidade or config.ativo else None
    propriedade_registo = _propriedades_visiveis(request.user).first()

    if request.GET.get('cidade') and dados_clima and not dados_clima.get('erro'):
        _guardar_registo_e_alerta(propriedade_registo, dados_clima)
        if propriedade_registo:
            messages.success(request, f"Dados meteorologicos guardados para {propriedade_registo.nome}.")

    return render(request, 'meteorologia/previsao.html', {
        'dados_clima': dados_clima,
        'config': config,
        'cidade_pesquisada': cidade,
        'propriedade_registo': propriedade_registo,
        'localidades_angola': LOCALIDADES_AGRICOLAS_ANGOLA,
    })


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_alertas(request):
    """Lista os alertas meteorológicos."""
    user = request.user
    alertas = Alerta.objects.filter(propriedade__in=_propriedades_visiveis(user))
    busca = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    severidade = request.GET.get('severidade', '').strip()
    estado = request.GET.get('estado', '').strip()
    if busca:
        alertas = alertas.filter(Q(propriedade__nome__icontains=busca) | Q(mensagem__icontains=busca))
    if tipo:
        alertas = alertas.filter(tipo=tipo)
    if severidade:
        alertas = alertas.filter(severidade=severidade)
    if estado == 'nao_lido':
        alertas = alertas.filter(lido=False)
    elif estado == 'lido':
        alertas = alertas.filter(lido=True)

    return render(request, 'meteorologia/lista_alertas.html', {
        'alertas': alertas,
        'filtros': {'q': busca, 'tipo': tipo, 'severidade': severidade, 'estado': estado},
        'tipos_alerta': Alerta.TIPO_CHOICES,
        'severidades': Alerta.SEVERIDADE_CHOICES,
    })


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def marcar_alerta_lido(request, pk):
    """Marca um alerta como lido."""
    alerta = get_object_or_404(Alerta.objects.filter(propriedade__in=_propriedades_visiveis(request.user)), pk=pk)
    alerta.lido = True
    alerta.save()
    messages.success(request, 'Alerta marcado como lido.')
    return redirect('meteorologia:lista_alertas')


@login_required
@perfil_required('admin', 'consultor', 'analista', 'tecnico', 'agricultor')
def lista_registros(request):
    """Lista os registros de clima históricos."""
    user = request.user
    registros = RegistroClima.objects.filter(propriedade__in=_propriedades_visiveis(user))
    busca = request.GET.get('q', '').strip()
    if busca:
        registros = registros.filter(Q(propriedade__nome__icontains=busca) | Q(descricao__icontains=busca))
    ultimos = list(registros.order_by('-data')[:12])
    ultimos.reverse()
    grafico = {
        'labels': [r.data.strftime('%d/%m %H:%M') for r in ultimos],
        'temperatura': [float(r.temperatura) if r.temperatura is not None else None for r in ultimos],
        'humidade': [float(r.humidade) if r.humidade is not None else None for r in ultimos],
        'vento': [float(r.vento_velocidade) if r.vento_velocidade is not None else None for r in ultimos],
    }

    return render(request, 'meteorologia/lista_registros.html', {
        'registros': registros,
        'grafico': grafico,
        'filtros': {'q': busca},
    })
