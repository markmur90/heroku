from django.contrib import admin
from api.configuraciones_api.models import ConfiguracionAPI

@admin.register(ConfiguracionAPI)
class ConfiguracionAPIAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'entorno', 'valor', 'activo')
    list_filter = ('entorno', 'activo')
    search_fields = ('nombre', 'valor', 'descripcion')
    list_editable = ('valor', 'entorno', 'activo')
    ordering = ('entorno', 'nombre')
    readonly_fields = ()

    def valor_resumido(self, obj):
        return (obj.valor[:60] + '...') if len(obj.valor) > 60 else obj.valor
    valor_resumido.short_description = 'Valor'
