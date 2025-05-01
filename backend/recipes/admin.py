from django.contrib import admin
from .models import (Tag, Ingredient, Recipe,
                     IngredientInRecipe, Favorite, ShoppingCart)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class IngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'fav_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    inlines = (IngredientInline,)

    @admin.display(description='В избранном')
    def fav_count(self, obj):
        return obj.in_favorites.count()