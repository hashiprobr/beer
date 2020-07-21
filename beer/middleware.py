from django.http import HttpResponse


class HealthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META['PATH_INFO'] == '/ping':
            return HttpResponse(b'pong')
        else:
            return self.get_response(request)
