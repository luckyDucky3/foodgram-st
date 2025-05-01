# backend/api/serializers.py
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreate,
    UserSerializer as DjoserUser,
)
from rest_framework import serializers
from users.models import User, Follow


class UserCreateSerializer(DjoserUserCreate):
    """POST /api/users/ (регистрация)."""
    class Meta(DjoserUserCreate.Meta):
        model = User
        # пароль обязателен ‒ указываем все поля из схемы
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class UserSerializer(DjoserUser):
    """Объект User в списке/деталях."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUser.Meta):
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj) -> bool:
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()
