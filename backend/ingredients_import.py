
import csv
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()

from recipes.models import Ingredient  # noqa

print('Importing ingredients...')

with open('../data/ingredients.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        name, measurement_unit = row
        Ingredient.objects.get_or_create(
            name=name.strip(),
            measurement_unit=measurement_unit.strip()
        )

print('Ingredients imported successfully!')