# backend/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Кастомный пользователь, авторизация по e-mail."""
    email = models.EmailField('e-mail', unique=True)
    avatar = models.ImageField(
        'Аватар', upload_to='users/avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Follow(models.Model):
    """Подписки «кто-на-кого»."""
    user = models.ForeignKey(
        User, related_name='follower', on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, related_name='following', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_follow'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='not_self_follow'),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} → {self.author}'

