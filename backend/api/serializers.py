import base64

from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.core.files.base import ContentFile

from recipes.models import (Tag, Recipe, IngredientInRecipe,
                            ShoppingCart, Favorite, Ingredient)
from users.models import User, Subscription


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserGetSerializer(UserSerializer):
    """Сериализатор для просмотра профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Subscription.objects.filter(
            author=obj, user=request.user
        ).exists()


class UserWithRecipesSerializer(UserGetSerializer):
    """Сериализатор для просмотра пользователя с рецептами."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = UserGetSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, object):
        request = self.context.get('request')
        context = {'request': request}
        recipe_limit = request.query_params.get('recipe_limit')
        queryset = object.recipes.all()
        if recipe_limit:
            queryset = queryset[:int(recipe_limit)]

        return RecipeShortSerializer(queryset, context=context, many=True).data


class UserPostSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get("password")

        validate_password(password, user)
        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = ('author', 'user', )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['author', 'user', ],
                message="Вы уже подписаны на этого пользователя"
            )
        ]

    def create(self, validated_data):
        return Subscription.objects.create(
            user=self.context.get('request').user, **validated_data)

    def validate_author(self, value):
        if self.context.get('request').user == value:
            raise serializers.ValidationError({
                'errors': 'Подписка на самого себя не возможна!'
            })
        return value


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient, где не требуется поле amount."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецептах."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeGetSerializer(serializers.ModelSerializer):
    '''Сериализатор для модели Recipe.
 Для GET запросов к эндпоинтам /recipe/ и /recipe/id/.
    '''
    tags = TagSerializer(many=True, read_only=True)
    author = UserGetSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='IngredientsInRecipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Favorite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(
            recipe=obj, user=request.user
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    '''Сериализатор для отображения краткой информации о рецептах.'''

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    author = UserGetSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientInRecipeSerializer(
        source='IngredientsInRecipe',
        many=True,
    )
    image = Base64ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            current_amount = ingredient.get('amount')
            ingredients_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=current_amount
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def validate(self, data):
        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {
                    'error': 'Время приготовления не должно быть менее 1 мин.'
                }
            )
        ingredients_list = []
        ingredients_in_recipe = data.get('IngredientsInRecipe')
        for ingredient in ingredients_in_recipe:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    {
                        'error': 'Ингредиентов не должно быть менее одного.'
                    }
                )
            ingredients_list.append(ingredient['ingredient']['id'])
        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                {
                    'error': 'Ингредиенты в рецепте не должны повторяться.'
                }
            )
        return data

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('IngredientsInRecipe')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('IngredientsInRecipe')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        instance.ingredients.clear()
        recipe = instance
        self.save_ingredients(recipe, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('recipe', 'user', )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['recipe', 'user', ],
                message='Этот рецепт уже добавлен в избранное.'
            )
        ]

    def create(self, validated_data):
        return Favorite.objects.create(
            user=self.context.get('request').user, **validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['recipe', 'user', ],
                message='Этот рецепт уже добавлен в список покупок.'
            )
        ]

    def create(self, validated_data):
        return ShoppingCart.objects.create(
            user=self.context.get('request').user, **validated_data)

