from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime
from io import BytesIO

from recipes.models import (Recipe, Ingredient,
                            Favorite, ShoppingCart,
                            RecipeIngredient)
from ..serializers.recipes import (RecipeListSerializer, RecipeWriteSerializer,
                                 IngredientSerializer,
                                 RecipeSerializer)
from ..permissions import IsAuthorOrReadOnly
from ..pagination import CustomPagination
from ..filters import IngredientFilter, RecipeFilter
import logging

logger = logging.getLogger(__name__)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Recipe.objects.all().prefetch_related(
            'recipe_ingredients__ingredient'
        ).select_related('author')

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def handle_favorite_or_shopping_cart(self, request, pk, model_class):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        verbose_name = model_class._meta.verbose_name

        if request.method == 'POST':
            obj, created = model_class.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': f'Рецепт "{recipe.name}" уже в {verbose_name}!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            recipe_serializer = RecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

        obj = get_object_or_404(model_class, user=user, recipe=recipe)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.handle_favorite_or_shopping_cart(request, pk, Favorite)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.handle_favorite_or_shopping_cart(request, pk, ShoppingCart)

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        
        recipes = Recipe.objects.filter(
            shopping_carts__user=user
        ).select_related('author')

        current_date = datetime.now().strftime('%d.%m.%Y')
        
        shopping_list = '\n'.join([
            f'Список покупок от {current_date}',
            '',
            'Продукты:',
            *[f'{i}. {item["ingredient__name"].capitalize()} '
              f'({item["ingredient__measurement_unit"]}) — {item["amount"]}'
              for i, item in enumerate(ingredients, 1)],
            '',
            'Рецепты:',
            *[f'• {recipe.name} (автор: {recipe.author.get_full_name() or recipe.author.username})'
              for recipe in recipes],
        ])

        response = FileResponse(
            BytesIO(shopping_list.encode('utf-8')),
            content_type='text/plain',
            filename='shopping_cart.txt'
        )
        return response

    @action(detail=True,
            methods=['get'],
            url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        
        short_url = request.build_absolute_uri(
            reverse('recipe_redirect', args=[pk])
        )
        
        return Response({'short-link': short_url})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None