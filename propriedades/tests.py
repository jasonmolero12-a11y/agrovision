from django.test import TestCase

# Create your tests here.

from datetime import date
from django.test import TestCase
from contas.models import Utilizador
from propriedades.models import Cultura, Propriedade, Talhao, RegistoProducao
from propriedades.views import _previsao_producao


class PrevisaoProducaoTests(TestCase):
    def setUp(self):
        self.user = Utilizador.objects.create_user(email='produtor-previsao@teste.local', password='Senha123forte', nome_completo='Produtor', tipo_utilizador='agricultor')
        self.cultura = Cultura.objects.create(nome='Cultura Previsão', ciclo='Anual')
        self.propriedade = Propriedade.objects.create(nome='Fazenda Previsão', proprietario=self.user, area_total=10)
        self.talhao = Talhao.objects.create(nome='Talhão Previsão', propriedade=self.propriedade, cultura=self.cultura, area=5)

    def test_previsao_usa_colheitas_reais_e_informa_confianca(self):
        for campanha, quantidade in [('2023/24', 1000), ('2024/25', 1200), ('2025/26', 1400)]:
            RegistoProducao.objects.create(talhao=self.talhao, campanha=campanha, data_colheita=date.today(), quantidade=quantidade, unidade='kg')
        previsao = _previsao_producao(self.propriedade)
        self.assertTrue(previsao['disponivel'])
        self.assertEqual(previsao['amostras'], 3)
        self.assertEqual(previsao['confianca'], 'média')
        self.assertGreater(previsao['valor'], 1200)

    def test_sem_colheita_nao_inventa_previsao(self):
        previsao = _previsao_producao(self.propriedade)
        self.assertFalse(previsao['disponivel'])
