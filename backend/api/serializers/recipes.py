import uuid
from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from api.serializers.users import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, RecipeShortLink
)
from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT, MAX_COOKING_TIME


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объектов ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Проверяет, что количество не меньше минимального значения."""
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                f'Количество ингредиента должно быть не менее {MIN_INGREDIENT_AMOUNT}'
            )
        return value


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )

    def _is_in_model(self, related_name):
        """Проверяет, находится ли рецепт в связанной модели пользователя."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated and
                related_name.filter(user=request.user).exists())

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное для пользователя."""
        return self._is_in_model(obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину покупок для пользователя."""
        return self._is_in_model(obj.shopping_carts)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )

    def validate(self, data):
        """Проверка всех данных."""
        ingredients = data.get('ingredients')

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Необходим как минимум один ингредиент'
            })

        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальными'
            })

        return data

    def validate_cooking_time(self, cooking_time):
        """Проверка времени приготовления."""
        if cooking_time < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время приготовления должно быть не менее {MIN_COOKING_TIME} минуты'
            )
        if cooking_time > MAX_COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления слишком большое'
            )
        return cooking_time

    def validate_image(self, image):
        """Проверка изображения."""
        if not image:
            raise serializers.ValidationError(
                'Изображение обязательно'
            )
        return image

    @transaction.atomic
    def create_ingredients(self, recipe, ingredients):
        """Создание объектов ингредиентов для рецепта."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        """Создание нового рецепта с ингредиентами."""
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта и его ингредиентов."""
        ingredients = validated_data.pop('ingredients')

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает представление в формате списка."""
        return RecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецептов для избранного и корзины покупок."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для коротких ссылок на рецепты."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Получение или создание короткой ссылки для рецепта."""
        request = self.context.get('request')
        short_link, created = RecipeShortLink.objects.get_or_create(
            recipe=obj,
            defaults={'slug': uuid.uuid4().hex[:6]}
        )

        url = reverse('redirect_short_link', kwargs={'slug': short_link.slug})
        if request:
            return request.build_absolute_uri(url)
        return url

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'short_link' in data:
            data['short-link'] = data.pop('short_link')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        """Возвращает представление рецепта."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину покупок'
            )
        ]

    def to_representation(self, instance):
        """Возвращает представление рецепта."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
