from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField
from recipes.models import Recipe
from users.models import User, Subscription


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    email = serializers.EmailField(
        required=True,
        max_length=254
    )

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar', 'password'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_email(self, value):
        """Валидация email на уникальность."""
        if (
            User.objects.filter(email=value).exists() and
            self.context.get('request') and
            self.context['request'].method == 'POST'
        ):
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return value

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на этого пользователя."""
        request = self.context.get('request')
        return request and request.user.is_authenticated and request.user.subscriptions.filter(
            author=obj
        ).exists()

    def to_representation(self, instance):
        """Переопределение: не возвращать пароль в ответе."""
        result = super().to_representation(instance)
        result.pop('password', None)
        return result


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор рецепта для подписок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и валидации подписок."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора'
            )
        ]

    def validate(self, data):
        """Валидация подписки."""
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )
        return data

    def to_representation(self, instance):
        """Представление данных автора после успешной подписки."""
        return UserSubscriptionSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок пользователя с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получить рецепты пользователя."""
        request = self.context.get('request')
        recipes = obj.recipes.all()

        try:
            limit = request.query_params.get('recipes_limit')
            if limit:
                recipes = recipes[:int(limit)]
        except (ValueError, TypeError):
            pass

        serializer = RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """Получить количество рецептов пользователя."""
        return obj.recipes.count()


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        """Возвращает полный URL к аватару пользователя."""
        request = self.context.get('request')
        avatar_url = instance.avatar.url if instance.avatar else None
        if avatar_url and request:
            avatar_url = request.build_absolute_uri(avatar_url)
        return {'avatar': avatar_url}
        