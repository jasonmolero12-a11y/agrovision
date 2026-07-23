from pathlib import Path

from django.db import migrations


def validar_demonstracao(apps, schema_editor):
    Propriedade = apps.get_model('propriedades', 'Propriedade')
    Talhao = apps.get_model('propriedades', 'Talhao')
    RegistoProducao = apps.get_model('propriedades', 'RegistoProducao')
    propriedade = Propriedade.objects.filter(nome='Fazenda Cristalina').first()
    # Bancos de testes nascem sem os utilizadores de demonstração; nesse caso,
    # os próprios TestCases criam os seus cenários isolados.
    if not propriedade:
        return
    if Talhao.objects.filter(propriedade=propriedade).count() != 3:
        raise RuntimeError('A Fazenda Cristalina deve possuir exatamente três talhões.')
    if RegistoProducao.objects.filter(talhao__propriedade=propriedade).count() != 3:
        raise RuntimeError('A Fazenda Cristalina deve possuir três registos de produção.')

    base_dir = Path(__file__).resolve().parents[2]
    destino = base_dir / 'relatorios' / 'Relatorio_Funcionamento_APIs_AgroVision_Fazenda_Cristalina.docx'
    if not destino.exists():
        from scripts.gerar_relatorio_api_cristalina import gerar_relatorio
        destino = gerar_relatorio(base_dir)
    from zipfile import ZipFile
    with ZipFile(destino) as arquivo:
        documento_xml = arquivo.read('word/document.xml').decode('utf-8')
    if 'Funcionamento das APIs' not in documento_xml or 'Fazenda Cristalina' not in documento_xml:
        raise RuntimeError('O relatório das APIs foi gerado sem as secções obrigatórias.')
    if '<w:tbl>' not in documento_xml:
        raise RuntimeError('O relatório das APIs deve conter a tabela dos três talhões.')


class Migration(migrations.Migration):
    dependencies = [
        ('propriedades', '0008_fazenda_cristalina_demonstracao'),
    ]

    operations = [
        migrations.RunPython(validar_demonstracao, migrations.RunPython.noop),
    ]
