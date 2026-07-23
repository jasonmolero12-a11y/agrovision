from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador


class FluxoDosUtilizadoresDaApresentacaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.messi = Utilizador.objects.create_user(
            email='messi.fluxo@teste.ao', password='Teste123!',
            nome_completo='Messi', tipo_utilizador='cliente',
        )
        cls.enock = Utilizador.objects.create_user(
            email='enock.fluxo@teste.ao', password='Teste123!',
            nome_completo='Enock', tipo_utilizador='agricultor',
        )
        cls.ado = Utilizador.objects.create_user(
            email='ado.fluxo@teste.ao', password='Teste123!',
            nome_completo='Ado', tipo_utilizador='consultor',
        )
        cls.priscila = Utilizador.objects.create_user(
            email='priscila.fluxo@teste.ao', password='Teste123!',
            nome_completo='Priscila', tipo_utilizador='analista',
        )
        cls.garcia = Utilizador.objects.create_user(
            email='garcia.fluxo@teste.ao', password='Teste123!',
            nome_completo='Garcia', tipo_utilizador='tecnico',
        )

    def test_01_cliente_messi(self):
        self.client.force_login(self.messi)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('propriedades:mercado')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:nova_recomendacao')).status_code, 302)

    def test_02_agricultor_enock(self):
        self.client.force_login(self.enock)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('propriedades:nova')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:consultoria_api_agricultor')).status_code, 200)

    def test_03_consultor_ado(self):
        self.client.force_login(self.ado)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:nova_recomendacao')).status_code, 200)

    def test_04_analista_priscila(self):
        self.client.force_login(self.priscila)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:nova_recomendacao')).status_code, 302)

    def test_05_tecnico_garcia(self):
        self.client.force_login(self.garcia)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:nova_visita')).status_code, 200)
        self.assertEqual(self.client.get(reverse('consultoria:nova_praga')).status_code, 200)
