from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador
from propriedades.models import Propriedade, Talhao, Cultura, RegistoProducao
from consultoria.models import Recomendacao
from .views import _contexto_limitado_chatbot, _resposta_programada


class ClienteCompradorTests(TestCase):
    def setUp(self):
        self.cliente = Utilizador.objects.create_user(email='comprador@teste.ao', password='Teste123!', nome_completo='Comprador Teste', tipo_utilizador='cliente')
        self.agricultor = Utilizador.objects.create_user(email='agricultor@teste.ao', password='Teste123!', nome_completo='Agricultor Teste', tipo_utilizador='agricultor')
        self.consultor = Utilizador.objects.create_user(email='consultor@teste.ao', password='Teste123!', nome_completo='Consultor Teste', tipo_utilizador='consultor')
        self.propriedade = Propriedade.objects.create(nome='Fornecedor Teste', proprietario=self.agricultor)
        self.propriedade.clientes_autorizados.add(self.cliente)
        cultura = Cultura.objects.create(nome='Milho Teste', ciclo='Anual')
        talhao = Talhao.objects.create(propriedade=self.propriedade, nome='Talhão Teste', cultura=cultura)
        self.rascunho = Recomendacao.objects.create(talhao=talhao, consultor=self.consultor, texto_recomendacao='Rascunho', status='rascunho')
        self.emitida = Recomendacao.objects.create(talhao=talhao, consultor=self.consultor, texto_recomendacao='Emitida', status='emitida')

    def test_painel_cliente_mostra_funcoes_de_comprador(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('dashboard:home'))
        self.assertContains(response, 'Cliente Comprador')
        self.assertContains(response, 'Fornecedores e Produção')
        self.assertNotContains(response, '>Talhões<')
        self.assertNotContains(response, '>Visitas Técnicas<')

    def test_contexto_chatbot_cliente_nao_e_agricultor(self):
        contexto = _contexto_limitado_chatbot(self.cliente)
        self.assertEqual(contexto['perfil'], 'Cliente Comprador')
        self.assertEqual(contexto['resumo']['fornecedores_autorizados'], 1)
        self.assertNotIn('relatorios_emitidos', contexto['resumo'])
        self.assertIn('pedidos de compra', contexto['atalhos'])

    def test_painel_agricultor_nao_expoe_pdf_de_rascunho(self):
        self.client.force_login(self.agricultor)
        response = self.client.get(reverse('dashboard:home'))
        self.assertNotContains(response, reverse('consultoria:pdf_recomendacao', args=[self.rascunho.pk]))
        self.assertContains(response, reverse('consultoria:pdf_recomendacao', args=[self.emitida.pk]))


class GuiaAgricolaChatbotTests(TestCase):
    def test_chatbot_guia_agricultor_sobre_plantio(self):
        contexto = {'perfil': 'Agricultor', 'resumo': {}, 'atalhos': []}
        resposta = _resposta_programada('Como plantar milho?', contexto)
        self.assertIn('Passo 1', resposta)
        self.assertIn('Passo 6', resposta)
        self.assertIn('sementes sadias', resposta)

    def test_guia_nao_substitui_diagnostico(self):
        contexto = {'perfil': 'Agricultor', 'resumo': {}, 'atalhos': []}
        resposta = _resposta_programada('Que adubo devo usar no solo?', contexto)
        self.assertIn('análise', resposta.lower())
        self.assertIn('não indique dose', resposta.lower())

    def test_corrige_erro_comum_e_explica_tomate(self):
        contexto = {'perfil': 'Cliente Comprador', 'resumo': {}, 'atalhos': []}
        resposta = _resposta_programada('O que é temote e como cultivo isso?', contexto)
        self.assertIn('tomate é uma hortaliça', resposta.lower())
        self.assertIn('Passo 1', resposta)
        self.assertIn('Passo 6', resposta)

    def test_guia_agricola_funciona_para_todos_os_perfis(self):
        for perfil in ['Administrador', 'Consultor Agricola', 'Tecnico de Campo', 'Analista de Dados']:
            contexto = {'perfil': perfil, 'resumo': {}, 'atalhos': []}
            resposta = _resposta_programada('Como cultivar soja?', contexto)
            self.assertIn('soja', resposta.lower())
            self.assertIn('Passo 1', resposta)
