"""Registo dos modelos de Propriedades no painel admin."""

from django.contrib import admin
from .models import Cultura, Propriedade, Talhao, RegistoProducao, PedidoCompra


@admin.register(Cultura)
class CulturaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ciclo', 'epoca_plantio')
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Propriedade)
class PropriedadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'proprietario', 'consultor_responsavel', 'tecnico_responsavel', 'analista_responsavel', 'area_total', 'localizacao', 'exposta_para_clientes')
    list_filter = ('exposta_para_clientes', 'consultor_responsavel', 'tecnico_responsavel', 'analista_responsavel', 'clientes_autorizados')
    filter_horizontal = ('clientes_autorizados', 'favoritada_por')
    search_fields = ('nome', 'localizacao', 'proprietario__nome_completo')
    ordering = ('nome',)


@admin.register(Talhao)
class TalhaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'propriedade', 'cultura', 'area', 'tipo_solo')
    list_filter = ('cultura', 'propriedade')
    search_fields = ('nome', 'propriedade__nome')
    ordering = ('propriedade', 'nome')


@admin.register(RegistoProducao)
class RegistoProducaoAdmin(admin.ModelAdmin):
    list_display = ('talhao', 'campanha', 'data_colheita', 'quantidade', 'unidade', 'qualidade', 'estado_comercial')
    list_filter = ('estado_comercial', 'campanha', 'unidade', 'data_colheita')
    search_fields = ('talhao__nome', 'talhao__propriedade__nome', 'campanha')


@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'propriedade', 'quantidade_pretendida', 'status', 'resposta_agricultor', 'criado_em')
    list_filter = ('status', 'resposta_agricultor', 'criado_em')
    search_fields = ('cliente__nome_completo', 'cliente__email', 'propriedade__nome', 'contacto')
    readonly_fields = ('criado_em', 'atualizado_em')
