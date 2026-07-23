"""Integração opcional com IA externa para o AgroVision."""

import requests

from .models import ConfiguracaoAPI


def gerar_texto_ia(prompt, contexto='', timeout=60, pesquisa_web=False):
    """
    Tenta gerar texto com Gemini.

    Retorna None se a IA não estiver configurada, se não houver internet ou se
    a API devolver erro. As views usam esse None para aplicar o fallback local.
    """
    config = ConfiguracaoAPI.carregar()
    if not config.ia_ativo or config.ia_provedor != 'gemini' or not config.ia_api_key:
        return None

    modelo = (config.ia_modelo or 'gemini-1.5-flash').strip()
    base = (config.ia_url_base or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')
    url = f'{base}/models/{modelo}:generateContent'
    params = {'key': config.ia_api_key}
    conteudo = (
        "Responda em português claro, com linguagem técnica agrícola simples. "
        "Não invente dados; use apenas o contexto recebido e indique quando algo for estimado.\n\n"
        f"Contexto:\n{contexto}\n\nPedido:\n{prompt}"
    )
    payload = {
        'contents': [
            {'parts': [{'text': conteudo}]}
        ],
        'generationConfig': {
            'temperature': 0.35,
            'maxOutputTokens': 700,
        },
    }
    if pesquisa_web:
        # O Gemini decide quando a pesquisa melhora a resposta e devolve texto
        # fundamentado em resultados atuais do Google Search.
        payload['tools'] = [{'google_search': {}}]

    try:
        response = requests.post(url, params=params, json=payload, timeout=timeout)
        if pesquisa_web and response.status_code >= 400:
            # Modelos antigos podem não aceitar google_search. Nesse caso, o
            # assistente continua disponível, sem pesquisa, em vez de falhar.
            payload.pop('tools', None)
            response = requests.post(url, params=params, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        texto = ''.join(part.get('text', '') for part in parts).strip()
        return texto or None
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None
