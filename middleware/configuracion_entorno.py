from api.configuraciones_api.loader import cargar_variables_entorno

class ConfiguracionPorSesionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cargar_variables_entorno(request=request)
        return self.get_response(request)
