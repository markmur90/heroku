from django.db import models

class ConfiguracionAPI(models.Model):
    ENTORNOS = [
        ("production", "Producción"),
        ("sandbox", "Sandbox"),
        ("local", "Local"),
    ]

    entorno = models.CharField(max_length=20, choices=ENTORNOS, default="production")
    nombre = models.CharField(max_length=100)
    valor = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'configuraciones_api'
        verbose_name = 'Configuración API'
        verbose_name_plural = 'Configuraciones API'
        unique_together = ('nombre', 'entorno')

    def __str__(self):
        return f'{self.nombre} [{self.entorno}]'
    
    
