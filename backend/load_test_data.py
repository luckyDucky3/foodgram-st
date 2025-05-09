import json
import os
import random
from PIL import Image
import io
from base64 import b64encode

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class Command(BaseCommand):
    """Django command to load test data for development."""

    help = 'Load test data for development'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Creating test users...')
            users = []
            for i in range(1, 4):
                user, created = User.objects.get_or_create(
                    username=f'user{i}',
                    defaults={
                        'email': f'user{i}@example.com',
                        'first_name': f'User{i}',
                        'last_name': f'Test{i}',
                        'password': f'password{i}',
                    }
                )
                if created:
                    user.set_password(f'password{i}')
                    user.save()
                    users.append(user)
                    self.stdout.write(f'Created user: {user.username}')
                else:
                    users.append(user)
                    self.stdout.write(f'User already exists: {user.username}')

            if Ingredient.objects.count() == 0:
                self.stdout.write(
                    'No ingredients found. Please load ingredients first with '
                    '`python manage.py import_ingredients`'
                )
                return

            self.stdout.write('Creating test recipes...')
            recipe_names = [
                'Паста карбонара', 'Омлет с сыром', 'Греческий салат',
                'Борщ', 'Пицца Маргарита', 'Жареная курица',
                'Тирамису', 'Тушеные овощи', 'Шашлык из свинины'
            ]

            descriptions = [
                'Классическое итальянское блюдо с беконом и сыром.',
                'Вкусный и быстрый завтрак с сыром и зеленью.',
                'Традиционный греческий салат с фетой и оливками.',
                'Традиционный украинский суп со свеклой и капустой.',
                'Классическая итальянская пицца с томатами и моцареллой.',
                'Сочная жареная курица с хрустящей корочкой.',
                'Итальянский десерт с кофе и маскарпоне.',
                'Полезное блюдо из сезонных овощей.',
                'Маринованное мясо, жаренное на углях.'
            ]

            def generate_test_image():
                placeholder_path = os.path.join(
                    settings.BASE_DIR, '../frontend/build/logo192.png'
                )
                if os.path.exists(placeholder_path):
                    with open(placeholder_path, 'rb') as f:
                        return SimpleUploadedFile(
                            'test_image.png',
                            f.read(),
                            content_type='image/png'
                        )
                else:
                    self.stdout.write(
                        f'Warning: Image not found at {placeholder_path}')
                    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    return SimpleUploadedFile(
                        'test_image.png',
                        img_bytes.getvalue(),
                        content_type='image/png'
                    )

            ingredients = list(Ingredient.objects.all())

            for i, name in enumerate(recipe_names):
                user = random.choice(users)
                cooking_time = random.randint(10, 120)

                recipe, created = Recipe.objects.get_or_create(
                    name=name,
                    defaults={
                        'author': user,
                        'text': descriptions[i],
                        'cooking_time': cooking_time,
                        'image': generate_test_image(),
                    }
                )

                if created:
                    num_ingredients = random.randint(3, 8)
                    selected_ingredients = random.sample(
                        ingredients, num_ingredients)

                    for ingredient in selected_ingredients:
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=ingredient,
                            amount=random.randint(1, 500)
                        )

                    self.stdout.write(f'Created recipe: {recipe.name}')
                else:
                    self.stdout.write(f'Recipe already exists: {recipe.name}')

            self.stdout.write(self.style.SUCCESS(
                'Successfully loaded test data'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading test data: {e}')
            )
