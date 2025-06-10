import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from recipes.models import Ingredient
from collections import defaultdict


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON-файла с оптимизацией для большого объема данных'

    def handle(self, *args, **options):
        try:
            file_path = '/app/data/ingredients.json'
            
            self.stdout.write(f'Загрузка данных из файла {file_path}...')
            
            existing = {(item['name'], item['measurement_unit']): True 
                      for item in Ingredient.objects.all().values('name', 'measurement_unit')}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                result = Ingredient.objects.bulk_create([
                    Ingredient(**ingredient) 
                    for ingredient in json.load(f)
                    if (ingredient['name'], ingredient['measurement_unit']) not in existing], 
                    ignore_conflicts=True)
            
            created_count = len(result)
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно импортировано {created_count} новых ингредиентов')
            )
        except Exception as e:
            raise CommandError(f'Ошибка при импорте ингредиентов из файла {file_path}: {e}')