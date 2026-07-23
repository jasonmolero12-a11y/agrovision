from unittest.mock import Mock, patch

from django.test import TestCase

from .views import _descricao_codigo_tempo, obter_previsao_api, _guardar_registo_e_alerta


class MeteorologiaTestes(TestCase):
    def test_traduz_codigo_wmo(self):
        self.assertEqual(_descricao_codigo_tempo(0), 'Céu limpo')
        self.assertEqual(_descricao_codigo_tempo(63), 'Chuva moderada')

    @patch('meteorologia.views.gerar_texto_ia', return_value=None)
    @patch('meteorologia.views.requests.get')
    def test_open_meteo_retorna_condicao_e_analise(self, get_mock, _ia_mock):
        geo = Mock(); geo.json.return_value = {'results': [{'latitude': -8.84, 'longitude': 13.23, 'name': 'Luanda'}]}; geo.raise_for_status.return_value = None
        clima = Mock(); clima.raise_for_status.return_value = None
        clima.json.return_value = {'current': {'time': '2026-07-18T12:00', 'temperature_2m': 25.4, 'relative_humidity_2m': 72, 'wind_speed_10m': 13.2, 'precipitation': 0, 'weather_code': 2}, 'daily': {'time': ['2026-07-18', '2026-07-19'], 'temperature_2m_max': [27.0, 28.0], 'temperature_2m_min': [19.0, 20.0], 'precipitation_sum': [0.0, 1.0], 'precipitation_probability_max': [5, 20]}}
        get_mock.side_effect = [geo, clima]
        resultado = obter_previsao_api('Luanda')
        self.assertEqual(resultado['descricao'], 'Parcialmente nublado')
        self.assertEqual(resultado['resumo_7_dias']['chuva_total'], 1.0)
        self.assertIn('analise_agricola', resultado)
        self.assertEqual(len(resultado['previsao_7_dias']), 2)


class GeracaoAlertaTestes(TestCase):
    def setUp(self):
        from contas.models import Utilizador
        from propriedades.models import Propriedade
        self.agricultor = Utilizador.objects.create_user(email='alerta@teste.ao', password='Teste123!', nome_completo='Agricultor Alerta', tipo_utilizador='agricultor')
        self.propriedade = Propriedade.objects.create(nome='Fazenda Alerta', proprietario=self.agricultor)

    def test_calor_da_api_cria_alerta_automatico(self):
        from .models import Alerta, RegistroClima
        _guardar_registo_e_alerta(self.propriedade, {'temperatura': 36, 'humidade': 50, 'vento': 10, 'descricao': 'quente'})
        self.assertTrue(RegistroClima.objects.filter(propriedade=self.propriedade, temperatura=36).exists())
        self.assertTrue(Alerta.objects.filter(propriedade=self.propriedade, tipo='calor_extremo', lido=False).exists())

    def test_valores_normais_nao_criam_alerta(self):
        from .models import Alerta
        _guardar_registo_e_alerta(self.propriedade, {'temperatura': 28, 'humidade': 60, 'vento': 15, 'descricao': 'normal'})
        self.assertFalse(Alerta.objects.filter(propriedade=self.propriedade).exists())
