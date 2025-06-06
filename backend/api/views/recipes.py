from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Recipe, Tag, Ingredient,
                            Favorite, ShoppingCart,
                            RecipeIngredient, ShortLink)
from ..serializers.recipes import (RecipeListSerializer, RecipeWriteSerializer,
                                 IngredientSerializer, TagSerializer,
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
            'tags', 'recipe_ingredients__ingredient'
        ).select_related('author')

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if 'ingredients' not in request.data or not request.data['ingredients']:
            return Response(
                {'errors': 'Необходимо указать хотя бы один ингредиент!'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def _handle_model_action(self, request, pk, model_class, action_name, action_status):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if model_class.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': f'Рецепт уже {action_status}!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            model_class.objects.create(user=user, recipe=recipe)
            
            recipe_serializer = RecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

        model_item = model_class.objects.filter(user=user, recipe=recipe)
        if not model_item.exists():
            return Response(
                {'errors': f'Рецепт не {action_status}!'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        model_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._handle_model_action(
            request, pk, Favorite, 'избранное', 'в избранном'
        )

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._handle_model_action(
            request, pk, ShoppingCart, 'список покупок', 'в списке покупок'
        )

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(
                {'errors': 'Список покупок пуст!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')

        shopping_list = 'Список покупок:\n\n'
        for item in ingredients:
            shopping_list += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['amount']}\n"
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(detail=True,
            methods=['get'],
            url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        
        short_link = ShortLink.objects.filter(recipe=recipe).first()
        
        if not short_link:
            short_id = ShortLink.generate_short_id(recipe.id)
            while ShortLink.objects.filter(short_id=short_id).exists():
                short_id = ShortLink.generate_short_id(recipe.id)
            
            short_link = ShortLink.objects.create(
                recipe=recipe,
                short_id=short_id
            )
        
        domain = request.build_absolute_uri('/').rstrip('/')
        full_short_link = f"{domain}/s/{short_link.short_id}"
        
        return Response({"short-link": full_short_link})

def redirect_short_link(request, short_id):
    short_link = get_object_or_404(ShortLink, short_id=short_id)
    return redirect(f'/recipes/{short_link.recipe.id}/')  

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None