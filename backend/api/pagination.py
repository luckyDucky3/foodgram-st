from rest_framework.pagination import PageNumberPagination
from api.constants import DEFAULT_PAGE_SIZE, DEFAULT_MAX_PAGE_SIZE, LIMIT_QUERY_PARAM


class LimitPageNumberPagination(PageNumberPagination):
    """
    Класс пагинации, который обрабатывает параметр limit
    для указания размера страницы.
    """

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = LIMIT_QUERY_PARAM
    max_page_size = DEFAULT_MAX_PAGE_SIZE
