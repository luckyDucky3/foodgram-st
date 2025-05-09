from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, USERNAME_MAX_LENGTH


class User(AbstractUser):
    """Пользовательская модель User для Foodgram."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        _('email address'),
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        _('first name'),
        max_length=NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        _('last name'),
        max_length=NAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='users/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('user'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=_('author'),
    )

    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        ordering = ['user__username', 'author__username']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.author}'

    def clean(self):
        """Валидация на уровне модели для предотвращения самоподписки."""
        if self.user == self.author:
            raise ValidationError(_('You cannot subscribe to yourself'))
