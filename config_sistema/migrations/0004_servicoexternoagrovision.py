from django.db import migrations, models


def criar_servicos_padrao(apps, schema_editor):
    Servico = apps.get_model('config_sistema', 'ServicoExternoAgroVision')
    servicos = [
        {
            'codigo': 'gemini',
            'nome': 'Google Gemini',
            'tipo': 'inteligencia',
            'endpoint': 'https://generativelanguage.googleapis.com',
            'descricao': 'Assistência conversacional e explicações agrícolas.',
        },
        {
            'codigo': 'open-meteo',
            'nome': 'Open-Meteo',
            'tipo': 'meteorologia',
            'endpoint': 'https://api.open-meteo.com/v1/forecast',
            'descricao': 'Condições e previsões meteorológicas.',
        },
        {
            'codigo': 'nasa-power',
            'nome': 'NASA POWER Daily',
            'tipo': 'meteorologia',
            'endpoint': 'https://power.larc.nasa.gov/api/temporal/daily/point',
            'descricao': 'Séries meteorológicas e agroclimáticas históricas.',
        },
        {
            'codigo': 'soilgrids',
            'nome': 'ISRIC SoilGrids',
            'tipo': 'solo',
            'endpoint': 'https://rest.isric.org/soilgrids/v2.0/properties/query',
            'descricao': 'Propriedades estimadas do solo por coordenadas.',
        },
        {
            'codigo': 'sentinel-hub',
            'nome': 'Copernicus Sentinel-2',
            'tipo': 'satelite',
            'endpoint': 'https://sh.dataspace.copernicus.eu/process/v1',
            'descricao': 'Processamento de imagens Sentinel-2.',
        },
        {
            'codigo': 'faostat',
            'nome': 'FAOSTAT',
            'tipo': 'agricultura',
            'endpoint': 'https://fenixservices.fao.org/faostat/api/v1',
            'descricao': 'Indicadores estatísticos agrícolas da FAO.',
        },
    ]
    for dados in servicos:
        Servico.objects.update_or_create(codigo=dados['codigo'], defaults=dados)


class Migration(migrations.Migration):
    dependencies = [('config_sistema', '0003_configuracaoapi_cadastro_senha_exigir_letra_and_more')]

    operations = [
        migrations.CreateModel(
            name='ServicoExternoAgroVision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.SlugField(max_length=60, unique=True)),
                ('nome', models.CharField(max_length=120)),
                ('tipo', models.CharField(choices=[('meteorologia', 'Meteorologia'), ('inteligencia', 'Inteligência artificial'), ('solo', 'Dados de solo'), ('satelite', 'Imagens de satélite'), ('agricultura', 'Dados agrícolas'), ('outro', 'Outro serviço')], max_length=30)),
                ('endpoint', models.URLField(blank=True, max_length=500)),
                ('chave_api', models.CharField(blank=True, help_text='Deixe vazia quando a API for pública e não exigir chave.', max_length=500)),
                ('ativo', models.BooleanField(default=True)),
                ('timeout_segundos', models.PositiveSmallIntegerField(default=20)),
                ('descricao', models.TextField(blank=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'serviço externo/API',
                'verbose_name_plural': 'serviços externos e APIs',
                'ordering': ('tipo', 'nome'),
            },
        ),
        migrations.RunPython(criar_servicos_padrao, migrations.RunPython.noop),
    ]
