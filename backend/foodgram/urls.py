from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from redirector.views import resolve_short_link


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<slug:slug>/', resolve_short_link, name='redirect_short_link')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
