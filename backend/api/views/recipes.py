import io
import os

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsOwnerOrReadOnly
from recipes.models import (
    Ingredient, Recipe, Favorite, ShoppingCart,
    RecipeIngredient, RecipeShortLink
)
from api.serializers import (
    IngredientSerializer, RecipeListSerializer,
    RecipeCreateUpdateSerializer, RecipeMinifiedSerializer,
    RecipeShortLinkSerializer, FavoriteSerializer, ShoppingCartSerializer
)
from recipes.utils import generate_shopping_list_pdf


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для модели ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для модели рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_recipe_relation(self, request, pk, model_class, serializer_class, error_message):
        """Общий метод для обработки отношений рецептов (избранное, корзина покупок)."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': recipe.id}
            serializer = serializer_class(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count = model_class.objects.filter(
            user=request.user, recipe=recipe
        ).delete()[0]

        if not deleted_count:
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить или удалить рецепт из избранного."""
        return self._handle_recipe_relation(
            request, pk,
            Favorite, FavoriteSerializer,
            'Рецепт не находится в избранном'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт из корзины покупок."""
        return self._handle_recipe_relation(
            request, pk,
            ShoppingCart, ShoppingCartSerializer,
            'Рецепт не находится в корзине покупок'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в формате PDF."""
        user = request.user

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients:
            return Response(
                {'message': 'Ваша корзина покупок пуста'},
                status=status.HTTP_200_OK
            )

        return generate_shopping_list_pdf(ingredients, user)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Сгенерировать короткую ссылку для рецепта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeShortLinkSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='find-by-slug/(?P<slug>[^/.]+)',
        permission_classes=[AllowAny],
    )
    def find_by_slug(self, request, slug=None):
        """Найти рецепт по короткому слагу и вернуть его ID."""
        try:
            recipe_link = get_object_or_404(RecipeShortLink, slug=slug)
            return Response({'id': recipe_link.recipe.id})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
