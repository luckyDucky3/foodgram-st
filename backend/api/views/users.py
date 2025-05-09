from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from users.models import User, Subscription
from api.serializers import (
    UserSubscriptionSerializer,
    SetAvatarSerializer,
    SubscriptionSerializer
)


class UserViewSet(DjoserUserViewSet):

    def get_permissions(self):
        """
        Настройка разрешений для разных действий.
        Для просмотра профилей разрешено всем, для других действий - как в базовом классе.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписаться на автора или отписаться от него."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            # Используем сериализатор для валидации и создания подписки
            data = {'user': user.id, 'author': author.id}
            serializer = SubscriptionSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE запрос - сразу выполняем удаление
        deleted_count = Subscription.objects.filter(
            user=user, author=author
        ).delete()[0]

        if not deleted_count:
            return Response(
                {'errors': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить все подписки пользователя."""
        user = request.user
        subscriptions = User.objects.filter(subscribers__user=user)

        page = self.paginate_queryset(subscriptions)
        serializer = UserSubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        """Обновить или удалить аватар пользователя."""
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SetAvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete(save=True)

        return Response(status=status.HTTP_204_NO_CONTENT)
    