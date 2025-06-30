class DetectarOficialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.username == "oficial_cuentas":
            request.session["usar_conexion_banco"] = "oficial"
        return self.get_response(request)
