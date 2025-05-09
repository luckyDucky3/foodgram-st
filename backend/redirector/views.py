from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from recipes.models import RecipeShortLink


def resolve_short_link(request, slug):
    """Преобразует короткую ссылку рецепта для перенаправления на фактический рецепт."""
    recipe_link = get_object_or_404(RecipeShortLink, slug=slug)
    recipe = recipe_link.recipe
    
    return HttpResponseRedirect(f'/recipes/{recipe.id}/')
