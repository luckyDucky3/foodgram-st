from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import display

from .models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, RecipeShortLink
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1
    verbose_name = _('Ingredient')
    verbose_name_plural = _('Ingredients')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'name')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorites_count',)

    @display(description=_('Added to favorites'))
    def favorites_count(self, obj):
        """Return the number of users who added the recipe to favorites."""
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(RecipeShortLink)
class RecipeShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'slug')
    search_fields = ('recipe__name', 'slug')
