from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на уровне объекта, позволяющее только владельцам объекта редактировать его.
    Предполагается, что экземпляр модели имеет атрибут `author`.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author == request.user
