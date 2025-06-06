from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

import logging
logger = logging.getLogger(__name__)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/', include('recipes.urls')),
]

logger.info(f"Main URL patterns: {urlpatterns}")

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)