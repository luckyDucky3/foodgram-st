from django.core import paginator
from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE


class CustomPagination(PageNumberPagination):
    django_paginator_class = paginator.Paginator
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
