from django.db import migrations


def sincronizar_gemini(apps, schema_editor):
    ConfiguracaoAPI = apps.get_model('config_sistema', 'ConfiguracaoAPI')
    Servico = apps.get_model('config_sistema', 'ServicoExternoAgroVision')
    configuracao = ConfiguracaoAPI.objects.first()
    if not configuracao:
        return

    defaults = {}
    if hasattr(configuracao, 'ia_api_key'):
        defaults['chave_api'] = configuracao.ia_api_key or ''
    if hasattr(configuracao, 'ia_ativo'):
        defaults['ativo'] = configuracao.ia_ativo
    if defaults:
        Servico.objects.filter(codigo='gemini').update(**defaults)


class Migration(migrations.Migration):
    dependencies = [('config_sistema', '0004_servicoexternoagrovision')]

    operations = [
        migrations.RunPython(sincronizar_gemini, migrations.RunPython.noop),
    ]
