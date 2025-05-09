from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, IngredientViewSet, RecipeViewSet, schema_view

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('schema/', schema_view, name='openapi-schema'),
]
