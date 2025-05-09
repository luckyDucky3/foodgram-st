from rest_framework.schemas import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    title="Foodgram API",
    description="API для проекта Foodgram 'Продуктовый помощник'",
    version="1.0.0",
    public=True,
    permission_classes=(permissions.AllowAny,),
)
