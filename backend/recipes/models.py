from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import UniqueConstraint

from users.models import User


class Ingredient(models.Model):
    '''Ингредиенты для составления рецептов с указанием единиц измерения.'''
    name = models.CharField(
        'Наименование ингредиента',
        max_length=200,
        validators=[
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z -]+$',
                message='Введите корректное имя/название'
            )
        ]
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=100
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} в {self.measurement_unit}'


class Tag(models.Model):
    '''Тэги.'''
    name = models.CharField(
        'Тэг',
        unique=True,
        max_length=200,
        validators=[
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z -]+$',
                message='Введите корректное имя/название'
            )
        ]
    )
    slug = models.SlugField(unique=True, db_index=True)
    color = models.CharField(
        'Цвет тэга в HEX формате',
        max_length=7,
        validators=[
            RegexValidator(
                regex=r'^#([A-Fa-f0-9]{3,6})$',
                message='Введите значение цвета в формате HEX! Пример:#FF0000'
            )
        ]
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    '''Рецепт.'''
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
        validators=[
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z -]+$',
                message='Введите корректное имя/название'
            )
        ]
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes'
    )
    cooking_time = models.IntegerField(
        'Время приготовления в минутах',
        validators=[
            MinValueValidator(
                1, 'Время приготовление должно быть не менее минуты'
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    '''Модель для связи рецепта и ингредиентов.'''
    recipe = models.ForeignKey(
        Recipe,
        related_name='IngredientsInRecipe',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='IngredientsInRecipe',
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        'Колличество ингредиента в данном рецепте.',
        validators=[
            MinValueValidator(
                1, 'Колличество ингредиента в рецептне не должно быть менее 1.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингридиент в рецепте '
        verbose_name_plural = 'Ингридиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient.name} в рецепте {self.recipe.name}'


class Favorite(models.Model):
    '''Избранные рецепты.'''
    user = models.ForeignKey(
        User,
        related_name='FavoriteRecipe',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='FavoriteRecipe',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]

    def __str__(self):
        return f'{self.recipe.name} в списке избанного у {self.user.username}'


class ShoppingCart(models.Model):
    '''Рецепты, добавленные в список покупок.'''
    user = models.ForeignKey(
        User,
        related_name='RecipeInShoppingList',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.recipe.name} в списке покупок у {self.user.username}'

