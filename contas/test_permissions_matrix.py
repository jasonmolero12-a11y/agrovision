from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from contas.models import Utilizador
from propriedades.models import Propriedade, Talhao, Cultura


class MatrizPermissoesEFormulariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Utilizador.objects.create_superuser(email='admin.matriz@teste.ao', password='Teste123!', nome_completo='Admin Matriz', tipo_utilizador='admin')
        cls.consultor = Utilizador.objects.create_user(email='consultor.matriz@teste.ao', password='Teste123!', nome_completo='Consultor Matriz', tipo_utilizador='consultor')
        cls.analista = Utilizador.objects.create_user(email='analista.matriz@teste.ao', password='Teste123!', nome_completo='Analista Matriz', tipo_utilizador='analista')
        cls.tecnico = Utilizador.objects.create_user(email='tecnico.matriz@teste.ao', password='Teste123!', nome_completo='Tecnico Matriz', tipo_utilizador='tecnico')
        cls.agricultor = Utilizador.objects.create_user(email='agricultor.matriz@teste.ao', password='Teste123!', nome_completo='Agricultor Matriz', tipo_utilizador='agricultor')
        cls.cliente = Utilizador.objects.create_user(email='cliente.matriz@teste.ao', password='Teste123!', nome_completo='Cliente Matriz', tipo_utilizador='cliente')
        cls.visitante = Utilizador.objects.create_user(email='visitante.matriz@teste.ao', password='Teste123!', nome_completo='Visitante Matriz', tipo_utilizador='visitante')
        cls.propriedade = Propriedade.objects.create(
            nome='Propriedade Matriz', proprietario=cls.agricultor,
            consultor_responsavel=cls.consultor,
            tecnico_responsavel=cls.tecnico,
            analista_responsavel=cls.analista,
        )
        cls.propriedade.clientes_autorizados.add(cls.cliente)
        cls.cultura = Cultura.objects.create(nome='Cultura Matriz', ciclo='Anual')
        cls.talhao = Talhao.objects.create(propriedade=cls.propriedade, nome='Talhao Matriz', cultura=cls.cultura)

    def entrar(self, user):
        self.client.force_login(user)

    def test_admin_tem_campos_e_centro_de_gestao(self):
        self.entrar(self.admin)
        painel = self.client.get(reverse('dashboard:home'))
        self.assertContains(painel, 'Centro de Gestão Completa')
        form = self.client.get(reverse('propriedades:nova'))
        for campo in ['name="nome"', 'name="proprietario"', 'name="clientes_autorizados"', 'name="consultor"', 'name="tecnico"', 'name="analista"', 'name="localizacao"', 'name="area_total"', 'name="foto_capa"']:
            self.assertContains(form, campo)

    @patch('consultoria.views._sugestao_recomendacao_automatica', return_value='Recomendacao de teste')
    def test_consultor_tem_recomendacao_mas_nao_cria_propriedade(self, _mock):
        self.entrar(self.consultor)
        self.assertEqual(self.client.get(reverse('propriedades:nova')).status_code, 302)
        form = self.client.get(reverse('consultoria:nova_recomendacao') + f'?talhao={self.talhao.pk}')
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, 'name="gerar_automaticamente"')
        self.assertContains(form, 'name="texto_recomendacao"')

    def test_analista_e_somente_leitura(self):
        self.entrar(self.analista)
        self.assertEqual(self.client.get(reverse('propriedades:lista')).status_code, 200)
        for rota in ['propriedades:nova', 'propriedades:novo_talhao', 'propriedades:nova_cultura', 'consultoria:nova_recomendacao', 'consultoria:nova_visita', 'consultoria:nova_praga']:
            self.assertEqual(self.client.get(reverse(rota)).status_code, 302, rota)

    def test_tecnico_tem_campos_de_campo(self):
        self.entrar(self.tecnico)
        visita = self.client.get(reverse('consultoria:nova_visita'))
        for campo in ['name="propriedade"', 'name="data"', 'name="tipo"', 'name="observacoes"', 'name="fotos"']:
            self.assertContains(visita, campo)
        praga = self.client.get(reverse('consultoria:nova_praga'))
        for campo in ['name="talhao"', 'name="nome"', 'name="severidade"', 'name="foto_diagnostico"']:
            self.assertContains(praga, campo)
        self.assertEqual(self.client.get(reverse('propriedades:nova')).status_code, 302)

    def test_agricultor_tem_producao_apenas_na_propriedade_dele(self):
        self.entrar(self.agricultor)
        form = self.client.get(reverse('propriedades:nova_producao', args=[self.propriedade.pk]))
        for campo in ['name="talhao"', 'name="campanha"', 'name="data_colheita"', 'name="quantidade"', 'name="unidade"', 'name="qualidade"', 'name="foto_colheita"']:
            self.assertContains(form, campo)
        self.assertEqual(self.client.get(reverse('consultoria:nova_recomendacao')).status_code, 302)

    def test_agricultor_edita_fazenda_e_talhao_proprios(self):
        self.entrar(self.agricultor)
        form = self.client.get(reverse('propriedades:editar', args=[self.propriedade.pk]))
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, 'name="nome"')
        self.assertNotContains(form, 'name="proprietario"')
        self.assertNotContains(form, 'name="consultor"')
        self.assertEqual(
            self.client.get(reverse('propriedades:editar_talhao', args=[self.talhao.pk])).status_code,
            200,
        )

    def test_agricultor_cria_propriedade_para_si_e_aguarda_equipa(self):
        self.entrar(self.agricultor)
        form = self.client.get(reverse('propriedades:nova'))
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, 'name="nome"')
        self.assertNotContains(form, 'name="proprietario"')
        resposta = self.client.post(reverse('propriedades:nova'), {
            'nome': 'Nova Fazenda do Agricultor',
            'localizacao': 'Luanda',
            'area_total': '12.50',
        })
        self.assertEqual(resposta.status_code, 302)
        criada = Propriedade.objects.get(nome='Nova Fazenda do Agricultor')
        self.assertEqual(criada.proprietario, self.agricultor)
        self.assertIsNone(criada.consultor_responsavel)
        self.assertIsNone(criada.tecnico_responsavel)
        self.assertIsNone(criada.analista_responsavel)

    def test_agricultor_nao_edita_fazenda_alheia(self):
        outro = Utilizador.objects.create_user(
            email='outro.agricultor@teste.ao', password='Teste123!',
            nome_completo='Outro Agricultor', tipo_utilizador='agricultor',
        )
        alheia = Propriedade.objects.create(nome='Fazenda Alheia', proprietario=outro)
        self.entrar(self.agricultor)
        self.assertEqual(self.client.get(reverse('propriedades:editar', args=[alheia.pk])).status_code, 404)

    def test_equipa_so_ve_propriedade_delegada(self):
        outro = Utilizador.objects.create_user(
            email='nao.delegada@teste.ao', password='Teste123!',
            nome_completo='Não Delegado', tipo_utilizador='agricultor',
        )
        nao_delegada = Propriedade.objects.create(nome='Não Delegada', proprietario=outro)
        for profissional in (self.consultor, self.tecnico, self.analista):
            self.client.force_login(profissional)
            resposta = self.client.get(reverse('propriedades:lista'))
            self.assertContains(resposta, self.propriedade.nome)
            self.assertNotContains(resposta, nao_delegada.nome)

    def test_cliente_e_comprador_sem_rotas_tecnicas(self):
        self.entrar(self.cliente)
        painel = self.client.get(reverse('dashboard:home'))
        self.assertContains(painel, 'Cliente Comprador')
        for rota in ['meteorologia:previsao', 'propriedades:lista_talhoes', 'consultoria:lista_visitas', 'consultoria:lista_pragas']:
            self.assertEqual(self.client.get(reverse(rota)).status_code, 302, rota)

    def test_visitante_tem_somente_solicitacao(self):
        self.entrar(self.visitante)
        form = self.client.get(reverse('contas:solicitar_perfil'))
        for campo in ['name="perfil_solicitado"', 'name="justificativa_solicitacao"', 'name="validacao_profissional"', 'name="cv_solicitacao"']:
            self.assertContains(form, campo)
        self.assertEqual(self.client.get(reverse('propriedades:lista')).status_code, 302)
