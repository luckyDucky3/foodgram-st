from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по имени (начало строки, без учета регистра)."""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов по различным полям."""

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация рецептов, находящихся в избранном пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов, находящихся в корзине покупок пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
