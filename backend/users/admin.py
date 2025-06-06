from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.db.models import Count

from .models import Subscription

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'display_avatar',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2'
            )
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscriptions_count=Count('subscriptions', distinct=True),
            subscribers_count=Count('subscribers', distinct=True)
        )

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description='Аватар')
    def display_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="30" height="30" />', obj.avatar.url)
        return "-"

    @admin.display(description='Рецептов', ordering='recipes_count')
    def recipes_count(self, obj):
        return obj.recipes_count

    @admin.display(description='Подписок', ordering='subscriptions_count')
    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    @admin.display(description='Подписчиков', ordering='subscribers_count')
    def subscribers_count(self, obj):
        return obj.subscribers_count


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')