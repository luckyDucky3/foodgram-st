from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag, 
    ShortLink 
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipe_count=Count('recipes'))
    
    @admin.display(description='Рецептов')
    def recipe_count(self, obj):
        """Показывает количество рецептов, использующих данный ингредиент"""
        return obj.recipe_count


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'get_favorites_count', 'display_ingredients', 'display_image')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'pub_date')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('pub_date', 'display_image')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').annotate(
            favorites_count=Count('in_favorites')
        )

    @admin.display(description='В избранном', ordering='favorites_count')
    def get_favorites_count(self, obj):
        return obj.favorites_count
    
    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        ingredients = obj.recipe_ingredients.select_related('ingredient')[:3]
        result = "<br>".join([
            f"{ing.ingredient.name}: {ing.amount} {ing.ingredient.measurement_unit}" 
            for ing in ingredients
        ])
        
        if obj.recipe_ingredients.count() > 3:
            result += "<br>..."
            
        return format_html(result)
        
    @admin.display(description='Изображение')
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" />', obj.image.url)
        return "-"


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'added_date')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')
    
    @admin.display(description='Дата добавления рецепта')
    def added_date(self, obj):
        """Отображает дату публикации рецепта"""
        return obj.recipe.pub_date


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color_display', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; width: 20px; height: 20px; ' 
            'display: inline-block; border: 1px solid gray;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Цвет'


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'recipe', 'created_at')
    search_fields = ('short_id', 'recipe__name')
    readonly_fields = ('short_id', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')