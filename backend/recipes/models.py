from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from users.models import User
from .constants import (
    MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT,
    INGREDIENT_NAME_MAX_LENGTH, MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH, SHORT_LINK_SLUG_MAX_LENGTH
)


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(
        _('name'),
        max_length=INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        _('measurement unit'),
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        verbose_name = _('ingredient')
        verbose_name_plural = _('ingredients')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('author'),
    )
    name = models.CharField(
        _('name'),
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        _('image'),
        upload_to='recipes/images/',
    )
    text = models.TextField(
        _('description'),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name=_('ingredients'),
    )
    cooking_time = models.PositiveSmallIntegerField(
        _('cooking time'),
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=_(
                    f'Cooking time should be at least {MIN_COOKING_TIME} minute'
                )
            )
        ],
    )
    pub_date = models.DateTimeField(
        _('publication date'),
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _('recipe')
        verbose_name_plural = _('recipes')
        ordering = ['-pub_date']
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для ингредиентов в рецепте с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('recipe'),
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('ingredient'),
    )
    amount = models.PositiveSmallIntegerField(
        _('amount'),
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=_(
                    f'Amount should be at least {MIN_INGREDIENT_AMOUNT}'
                )
            )
        ],
    )

    class Meta:
        verbose_name = _('recipe ingredient')
        verbose_name_plural = _('recipe ingredients')
        ordering = ['recipe', 'ingredient']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} - {self.amount} {self.ingredient.measurement_unit}'


class UserRecipeRelation(models.Model):
    """Абстрактная модель для связей пользователя и рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('user'),
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('recipe'),
    )

    class Meta:
        abstract = True
        ordering = ['recipe__name']

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):
    """Модель для избранных рецептов пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(UserRecipeRelation):
    """Модель для рецептов в корзине покупок пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = _('shopping cart item')
        verbose_name_plural = _('shopping cart items')
        default_related_name = 'shopping_carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_item'
            )
        ]


class RecipeShortLink(models.Model):
    """Модель для хранения коротких ссылок на рецепты."""

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link',
        verbose_name=_('recipe'),
    )
    slug = models.SlugField(
        _('slug'),
        max_length=SHORT_LINK_SLUG_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = _('recipe short link')
        verbose_name_plural = _('recipe short links')
        ordering = ['recipe__name']

    def __str__(self):
        return f'{self.recipe} - {self.slug}'
