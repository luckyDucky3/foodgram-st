import django_filters as filters
from django.db.models import Q
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Ingredient 


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)
    
    def filter_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author__id')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(shopping_carts__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')  