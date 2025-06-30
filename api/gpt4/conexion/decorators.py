from django.http import JsonResponse

def requiere_conexion_banco(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("usar_conexion_banco", False):
            return JsonResponse({"error": "🔌 Conexión bancaria desactivada"}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
