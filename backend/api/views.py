# backend/api/views.py
from rest_framework import mixins, viewsets, permissions
from djoser.views import UserViewSet as DjoserUserViewSet
from users.models import User

from .serializers import UserSerializer, UserCreateSerializer
from .pagination import LimitPageNumberPagination


class UserViewSet(DjoserUserViewSet):
    """
    /api/users/  (list, create)
    /api/users/{id}/  (retrieve)
    /api/users/me/  (extra action «me» из Djoser)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        # регистрация и listing доступны всем
        if self.action in ('create', 'list', 'retrieve'):
            return (permissions.AllowAny(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
