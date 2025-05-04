from django.contrib import admin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """ В админке возможность редактировать и удалять
    все данные о пользователях. Фильтрация по email и username.
    """
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'password',
        'role',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс для настройки отображения данных о подписках."""
    list_display = ('user', 'author')
