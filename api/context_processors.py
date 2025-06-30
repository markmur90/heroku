def entorno_actual(request):
    return {
        'entornos': ['local', 'sandbox', 'production'],
        'entorno_actual': request.session.get('entorno_actual', 'production')
    }
