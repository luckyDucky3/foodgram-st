from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'first_name',
        'last_name', 'is_staff', 'recipes_count', 'subscribers_count'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_queryset(self, request):
        """Оптимизированный queryset с аннотациями для подсчета."""

        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _recipes_count=Count('recipes', distinct=True),
            _subscribers_count=Count('subscribers', distinct=True)
        )
        return queryset

    @display(description=_('Recipes'))
    def recipes_count(self, obj):
        """Количество рецептов у пользователя."""

        return getattr(obj, '_recipes_count', 0)

    @display(description=_('Subscribers'))
    def subscribers_count(self, obj):
        """Количество подписчиков у пользователя."""

        return getattr(obj, '_subscribers_count', 0)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
