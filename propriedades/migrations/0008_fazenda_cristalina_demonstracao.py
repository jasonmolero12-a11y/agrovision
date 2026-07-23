from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.db import migrations


IMAGENS = {
    'fazenda': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-5a4001e3-2aba-420f-8eda-4a383aafdf89.jpg'),
    'mandioca_colheita': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-9f857ac6-cd01-46e0-8675-9966c7af71af.jpg'),
    'feijao_colheita': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-fce1bfc5-a890-4588-a9b6-f33b02061d1c.jpg'),
    'feijao_talhao': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-ca1a5825-8e17-4e7a-8083-f62d31c1ec1c.jpg'),
    'soja_colheita': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-438a2945-227d-4a98-959d-40fde6f8bf2e.webp'),
    'soja_talhao': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-b60874ea-7a08-44aa-ace1-8238342ad721.png'),
    'mandioca_talhao': Path(r'C:\Users\jason\AppData\Local\Temp\codex-clipboard-fe994132-37d0-4cfa-b246-02beed74c53e.jpg'),
}


def _utilizador(Utilizador, nome, tipo):
    return (
        Utilizador.objects.filter(nome_completo__iexact=nome, tipo_utilizador=tipo).first()
        or Utilizador.objects.filter(tipo_utilizador=tipo).first()
    )


def _guardar_imagem(obj, campo, caminho, nome):
    if caminho.exists() and not getattr(obj, campo):
        with caminho.open('rb') as origem:
            getattr(obj, campo).save(nome, File(origem), save=True)


def criar_demonstracao(apps, schema_editor):
    Utilizador = apps.get_model('contas', 'Utilizador')
    Cultura = apps.get_model('propriedades', 'Cultura')
    Propriedade = apps.get_model('propriedades', 'Propriedade')
    Talhao = apps.get_model('propriedades', 'Talhao')
    RegistoProducao = apps.get_model('propriedades', 'RegistoProducao')

    agricultor = _utilizador(Utilizador, 'Enock', 'agricultor')
    if not agricultor:
        return
    consultor = _utilizador(Utilizador, 'Ado', 'consultor')
    tecnico = _utilizador(Utilizador, 'Garcia', 'tecnico')
    analista = _utilizador(Utilizador, 'Priscila', 'analista')

    defaults_completos = {
        'proprietario': agricultor,
        'localizacao': 'Malanje, Malanje, Angola',
        'area_total': Decimal('96.50'),
        'descricao': 'Unidade demonstrativa de feijão, mandioca e soja para validação integral do AgroVision.',
        'exposta_para_clientes': True,
        'consultor_responsavel': consultor,
        'tecnico_responsavel': tecnico,
        'analista_responsavel': analista,
    }
    campos_propriedade = {campo.name for campo in Propriedade._meta.fields}
    defaults = {
        chave: valor for chave, valor in defaults_completos.items()
        if chave in campos_propriedade
    }
    propriedade, criada = Propriedade.objects.get_or_create(nome='Fazenda Cristalina', defaults=defaults)
    if not criada:
        for campo, valor in defaults.items():
            setattr(propriedade, campo, valor)
        propriedade.save()
    _guardar_imagem(propriedade, 'foto_capa', IMAGENS['fazenda'], 'fazenda-cristalina.jpg')

    configuracoes = [
        ('Feijão', 'Talhão Cristal Feijão', Decimal('24.50'), 'Franco-argiloso', 'feijao_talhao', 'feijao_colheita', Decimal('7800')),
        ('Mandioca', 'Talhão Raiz Cristalina', Decimal('38.00'), 'Arenoso bem drenado', 'mandioca_talhao', 'mandioca_colheita', Decimal('42000')),
        ('Soja', 'Talhão Horizonte Soja', Decimal('30.00'), 'Franco com matéria orgânica', 'soja_talhao', 'soja_colheita', Decimal('9600')),
    ]
    campos_producao = {campo.name for campo in RegistoProducao._meta.fields}
    for cultura_nome, talhao_nome, area, solo, foto_talhao, foto_colheita, quantidade in configuracoes:
        cultura, _ = Cultura.objects.get_or_create(nome=cultura_nome, defaults={'ciclo': 'Anual'})
        talhao, _ = Talhao.objects.get_or_create(
            propriedade=propriedade,
            nome=talhao_nome,
            defaults={
                'cultura': cultura, 'area': area, 'tipo_solo': solo,
                'data_plantio': date(2026, 3, 15),
            },
        )
        _guardar_imagem(talhao, 'foto_atual', IMAGENS[foto_talhao], f'{cultura_nome.lower()}-talhao{IMAGENS[foto_talhao].suffix}')

        kwargs = {'talhao': talhao}
        valores = {
            'campanha': '2026/2027',
            'data_colheita': date(2026, 7, 20),
            'quantidade': quantidade,
            'unidade': 'kg',
            'qualidade': 'Tipo A — colheita selecionada',
            'estado_comercial': 'disponivel',
            'observacoes': f'Produção demonstrativa de {cultura_nome} da Fazenda Cristalina.',
        }
        kwargs.update({chave: valor for chave, valor in valores.items() if chave in campos_producao})
        filtros = {'talhao': talhao}
        if 'campanha' in campos_producao:
            filtros['campanha'] = '2026/2027'
        producao, _ = RegistoProducao.objects.get_or_create(defaults=kwargs, **filtros)
        if 'foto' in campos_producao:
            _guardar_imagem(producao, 'foto', IMAGENS[foto_colheita], f'{cultura_nome.lower()}-colheita{IMAGENS[foto_colheita].suffix}')

    try:
        from scripts.gerar_relatorio_api_cristalina import gerar_relatorio
        gerar_relatorio(Path(__file__).resolve().parents[2])
    except Exception:
        # O cadastro não deve falhar se a biblioteca de documentos estiver ausente.
        pass


def remover_demonstracao(apps, schema_editor):
    Propriedade = apps.get_model('propriedades', 'Propriedade')
    Propriedade.objects.filter(nome='Fazenda Cristalina').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('propriedades', '0007_pedidocompra'),
    ]

    operations = [
        migrations.RunPython(criar_demonstracao, remover_demonstracao),
    ]
