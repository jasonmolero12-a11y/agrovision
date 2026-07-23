import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from contas.models import Utilizador
from propriedades.models import Cultura, Propriedade, Talhao


class CulturaLivreNoTalhaoTests(TestCase):
    def setUp(self):
        self.agricultor = Utilizador.objects.create_user(
            email='cultura.livre@teste.ao', password='Teste123!',
            nome_completo='Agricultor Cultura Livre', tipo_utilizador='agricultor',
        )
        self.propriedade = Propriedade.objects.create(
            nome='Fazenda Cultura Livre', proprietario=self.agricultor,
            localizacao='Cacuaco, Luanda',
        )
        self.client.force_login(self.agricultor)

    def test_formulario_usa_texto_livre_e_cria_cultura(self):
        formulario = self.client.get(reverse('propriedades:novo_talhao'))
        self.assertContains(formulario, 'name="cultura_nome"')
        self.assertNotContains(formulario, 'name="cultura"')

        resposta = self.client.post(reverse('propriedades:novo_talhao'), {
            'propriedade': self.propriedade.pk,
            'nome': 'Talhão Batata Doce',
            'cultura_nome': 'Batata-doce',
            'area': '2.5',
            'tipo_solo': 'Franco arenoso',
        })
        self.assertEqual(resposta.status_code, 302)
        talhao = Talhao.objects.get(nome='Talhão Batata Doce')
        self.assertEqual(talhao.cultura.nome, 'Batata-doce')

    def test_texto_com_mesmo_nome_reutiliza_cultura(self):
        existente = Cultura.objects.create(nome='Mandioca', ciclo='Anual')
        self.client.post(reverse('propriedades:novo_talhao'), {
            'propriedade': self.propriedade.pk,
            'nome': 'Talhão Mandioca',
            'cultura_nome': '  mandioca  ',
        })
        self.assertEqual(Talhao.objects.get(nome='Talhão Mandioca').cultura, existente)

    def test_foto_real_tst_pode_ser_usada_na_propriedade_e_talhao(self):
        fotos = [
            caminho for caminho in Path(settings.BASE_DIR).rglob('tst*')
            if caminho.is_file() and caminho.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
        ]
        self.assertTrue(fotos, 'Nenhuma fotografia iniciada por tst foi encontrada na pasta do projeto.')
        foto = fotos[0]
        conteudo = foto.read_bytes()
        with tempfile.TemporaryDirectory() as media_temporaria:
            with override_settings(MEDIA_ROOT=media_temporaria):
                self.propriedade.foto_capa = SimpleUploadedFile(
                    foto.name, conteudo, content_type='image/jpeg',
                )
                self.propriedade.save(update_fields=['foto_capa'])
                talhao = Talhao.objects.create(
                    propriedade=self.propriedade, nome='Talhão com Foto',
                    foto_atual=SimpleUploadedFile(
                        f'talhao-{foto.name}', conteudo, content_type='image/jpeg',
                    ),
                )
                self.assertTrue(self.propriedade.foto_capa.name)
                self.assertTrue(talhao.foto_atual.name)
