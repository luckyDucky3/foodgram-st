#!/usr/bin/env python
import os
import django
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()

from django.core.management import call_command


def main():
    """Сбор статических файлов."""
    print('Collecting static files...')
    call_command('collectstatic', '--noinput')
    print('Static files collected.')


if __name__ == '__main__':
    main()