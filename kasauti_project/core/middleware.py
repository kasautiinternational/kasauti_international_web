"""
Custom 404 middleware — Kasauti International.

Problem: /products/xyz/ jaise URLs ek URL pattern se MATCH ho jate hain,
par view andar se Http404 raise karta hai (unknown category / sub-category /
product). DEBUG=True me Django uske liye apna yellow debug page dikhata hai.

Ye middleware har raised Http404 ko pakad kar hamara brand 404 page
(templates/404.html) render karta hai — DEBUG=True aur False dono me.
Admin URLs (/admin/...) ko skip karta hai taaki Django admin ka apna
behaviour intact rahe.
"""

from django.http import Http404
from django.shortcuts import render


class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            # Django admin apna 404 khud handle kare
            if request.path.startswith('/admin/'):
                return None
            return render(request, '404.html', status=404)
        return None
