from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from .ia import gerar_texto_ia


class GeminiPesquisaWebTests(SimpleTestCase):
    def _config(self):
        return SimpleNamespace(
            ia_ativo=True,
            ia_provedor='gemini',
            ia_api_key='chave-teste',
            ia_modelo='gemini-2.5-flash',
            ia_url_base='',
        )

    @patch('config_sistema.ia.requests.post')
    @patch('config_sistema.ia.ConfiguracaoAPI.carregar')
    def test_pesquisa_web_envia_ferramenta_google_search(self, carregar, post):
        carregar.return_value = self._config()
        resposta = Mock(status_code=200)
        resposta.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Resposta agrícola atual.'}]}}],
        }
        post.return_value = resposta

        texto = gerar_texto_ia('Como plantar?', pesquisa_web=True)

        self.assertEqual(texto, 'Resposta agrícola atual.')
        self.assertEqual(post.call_args.kwargs['json']['tools'], [{'google_search': {}}])

    @patch('config_sistema.ia.requests.post')
    @patch('config_sistema.ia.ConfiguracaoAPI.carregar')
    def test_modelo_antigo_tenta_novamente_sem_pesquisa(self, carregar, post):
        carregar.return_value = self._config()
        rejeitada = Mock(status_code=400)
        aceite = Mock(status_code=200)
        aceite.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Fallback disponível.'}]}}],
        }
        post.side_effect = [rejeitada, aceite]

        texto = gerar_texto_ia('Pergunta', pesquisa_web=True)

        self.assertEqual(texto, 'Fallback disponível.')
        self.assertEqual(post.call_count, 2)
        self.assertNotIn('tools', post.call_args.kwargs['json'])
