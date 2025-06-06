import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from recipes.models import Ingredient
from collections import defaultdict


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON-файла с оптимизацией для большого объема данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5000,
            help='Размер пакета для массовой вставки записей'
        )

    def handle(self, *args, **options):
        try:
            file_path = '/app/data/ingredients.json'
            
            self.stdout.write(f'Загрузка данных из файла {file_path}...')
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
            
            existing = {(item['name'], item['measurement_unit']): True 
                      for item in Ingredient.objects.all().values('name', 'measurement_unit')}
            
            new_ingredients = [
                Ingredient(name=ingredient['name'], measurement_unit=ingredient['measurement_unit'])
                for ingredient in ingredients_data
                if (ingredient['name'], ingredient['measurement_unit']) not in existing
            ]
            
            result = Ingredient.objects.bulk_create(new_ingredients, ignore_conflicts=True)
            created_count = len(result)
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно импортировано {created_count} новых ингредиентов')
            )
        except Exception as e:
            raise CommandError(f'Ошибка при импорте ингредиентов из файла {file_path}: {e}')