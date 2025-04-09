from django.http import HttpResponseForbidden
from django.conf import settings

class RestrictBrowsableAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verifica si es una petición a la API navegable (HTML)
        if (request.path.startswith('/api/') and 
            request.META.get('HTTP_ACCEPT', '').find('text/html') != -1):
            
            # Obtén la IP del cliente
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
                
            # Verifica si la IP está permitida
            if ip not in settings.INTERNAL_IPS:
                return HttpResponseForbidden("Acceso a la API navegable restringido")
        
        return self.get_response(request)