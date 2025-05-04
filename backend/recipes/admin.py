from django.contrib import admin

from .models import (Recipe, Tag, IngredientInRecipe,
                     ShoppingCart, Favorite, Ingredient)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка отображения данных о рецептах
    в интерфейсе администратора.
    """
    inlines = (RecipeIngredientInline,)
    list_display = (
        'name', 'author', 'pub_date',
    )
    list_filter = ('name', 'author',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройки отображения данных о тэгах
    в интерфейсе администратора.
    """
    list_display = ('pk', 'name', 'slug', 'color',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка отображения данных об ингредиентах
    в интерфейсе администратора.
    """
    list_display = ('pk', 'name', 'measurement_unit')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройки отображения данных о рецептах,
    которые пользователи отмечают избранными.
    """
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройки отображения списка покупок."""

    list_display = ('user', 'recipe')