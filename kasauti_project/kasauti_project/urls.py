from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from core.views import serve_media, custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# Custom 404 page (DEBUG=False par active hota hai)
handler404 = 'core.views.custom_404'

# Serve uploaded media with HTTP Range support so <video> plays in Chrome.
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media),
    ]

# CATCH-ALL: DEBUG=True (local development) me bhi custom 404 page dikhane
# ke liye. Jo bhi URL upar kisi bhi pattern se match nahi hota
# (jaise /proper/), wo seedha brand 404 page par jayega.
# NOTE: ye HAMESHA sabse LAST me hona chahiye — warna media/admin
# jaise valid URLs bhi 404 par chale jayenge.
urlpatterns += [
    re_path(r'^.*$', custom_404),
]
