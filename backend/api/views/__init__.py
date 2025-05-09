from api.views.users import UserViewSet
from api.views.recipes import IngredientViewSet, RecipeViewSet
from api.views.schema import schema_view

__all__ = [
    'UserViewSet',
    'IngredientViewSet',
    'RecipeViewSet',
    'schema_view',
]
