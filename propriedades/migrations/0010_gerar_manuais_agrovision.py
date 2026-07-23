from pathlib import Path
from zipfile import ZipFile

from django.db import migrations


def gerar_e_validar(apps, schema_editor):
    from scripts.gerar_manuais_agrovision import gerar_manuais

    base_dir = Path(__file__).resolve().parents[2]
    arquivos = gerar_manuais(base_dir)
    obrigatorios = ['Manual de Utilização', 'AgroVision Funciona', 'Manual de Programação']
    for arquivo, texto in zip(arquivos, obrigatorios):
        # Um DOCX produzido apenas com texto pode ser bastante compacto por
        # causa da compressão ZIP. A validade real é confirmada abaixo ao
        # abrir o pacote e verificar o XML e os textos obrigatórios.
        if not arquivo.exists() or arquivo.stat().st_size < 500:
            raise RuntimeError(f'Manual não foi gerado corretamente: {arquivo.name}')
        with ZipFile(arquivo) as pacote:
            xml = pacote.read('word/document.xml').decode('utf-8')
        if texto not in xml:
            raise RuntimeError(f'Manual sem conteúdo obrigatório: {arquivo.name}')


class Migration(migrations.Migration):
    dependencies = [('propriedades', '0009_validar_demonstracao_cristalina')]
    operations = [migrations.RunPython(gerar_e_validar, migrations.RunPython.noop)]
