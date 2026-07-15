from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from core.views import serve_media, custom_404
from core.admin import admin_new_counts  # NEW: admin badge counts (JSON)
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from core.sitemaps import StaticViewSitemap, CategorySitemap, ProductSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    # NEW: admin sidebar badge counts — admin/ se PEHLE hona zaroori hai
    path('admin/new-counts/', admin_new_counts, name='admin_new_counts'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
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