from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe
from users.models import User


def post_and_delete_action(
        self, request, model_1, model_2, serializer, **kwargs
):
    """
    Действия добавления и удаления:
    рецепта в список покупок(model_1 == Recipe, model_2 == Shopping_list),
    рецепта в избранное(model_1 == Recipe, model_2 == Favorite)
    подписки на пользователей(model_1 == User, model_2 == Subscription)
    """
    object_1 = get_object_or_404(model_1, id=kwargs['pk'])
    data = request.data.copy()
    if model_1 == Recipe:
        data.update({'recipe': object_1.id})
    elif model_1 == User:
        data.update(
            {'author': object_1.id}
        )
    serializer = serializer(
        data=data, context={'request': request}
    )

    if request.method == "POST":
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            data=self.get_serializer(object_1).data
        )

    elif request.method == "DELETE" and model_1 == Recipe:
        object = model_2.objects.filter(
            recipe=object_1, user=request.user
        )
        if not object.exists():
            return Response(
                {'errors': 'В списке покупок(в избранном) нет этого рецепта.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == "DELETE" and model_1 == User:
        object = model_2.objects.filter(
            author=object_1, user=request.user
        )
        if not object.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)