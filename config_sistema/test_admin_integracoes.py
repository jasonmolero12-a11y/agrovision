from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador
from dashboard.views import _resposta_programada

from .models import ServicoExternoAgroVision


class AdminIntegracoesAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Utilizador.objects.create_superuser(
            email='admin.api@agrovision.ao',
            password='Teste123!',
            nome_completo='Administrador API',
        )

    def test_catalogo_inicial_contem_integracoes_principais(self):
        codigos = set(
            ServicoExternoAgroVision.objects.values_list('codigo', flat=True)
        )
        self.assertTrue(
            {'gemini', 'open-meteo', 'nasa-power', 'soilgrids', 'sentinel-hub', 'faostat'}.issubset(codigos)
        )

    def test_administrador_altera_endpoint_chave_estado_e_timeout(self):
        self.client.force_login(self.admin)
        servico = ServicoExternoAgroVision.objects.get(codigo='gemini')
        url = reverse(
            'admin:config_sistema_servicoexternoagrovision_change',
            args=[servico.pk],
        )
        resposta = self.client.post(
            url,
            {
                'codigo': servico.codigo,
                'nome': servico.nome,
                'tipo': servico.tipo,
                'endpoint': 'https://generativelanguage.googleapis.com',
                'chave_api': 'credencial-alterada-pelo-admin',
                'ativo': 'on',
                'timeout_segundos': '35',
                'descricao': 'Configuração administrável do chatbot.',
            },
        )
        self.assertEqual(resposta.status_code, 302)
        servico.refresh_from_db()
        self.assertEqual(servico.timeout_segundos, 35)
        self.assertEqual(servico.chave_api, 'credencial-alterada-pelo-admin')


class ChatbotPorPerfilTests(TestCase):
    def contexto(self, perfil):
        return {'perfil': perfil, 'resumo': {}, 'atalhos': ['ajuda']}

    def test_orienta_cada_tipo_de_utilizador(self):
        casos = {
            'Visitante': 'solicitar um perfil',
            'Cliente Comprador': 'Mercado Agrícola',
            'Agricultor': 'Consultoria Inteligente',
            'Consultor Agrícola': 'emitir recomendações',
            'Técnico de Campo': 'registar visitas',
            'Analista de Dados': 'analisar propriedades',
            'Administrador': 'serviços externos e APIs',
        }
        for perfil, trecho in casos.items():
            with self.subTest(perfil=perfil):
                resposta = _resposta_programada(
                    'Quais são minhas funções e como usar o sistema?',
                    self.contexto(perfil),
                )
                self.assertIn(trecho, resposta)
