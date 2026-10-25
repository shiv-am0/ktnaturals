class PrivateHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(("/owner/", "/admin/")):
            response["X-Robots-Tag"] = "noindex, nofollow"
            response["Cache-Control"] = "no-store, private"
        return response
