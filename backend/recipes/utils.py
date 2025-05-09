import io
import os
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_shopping_list_pdf(ingredients, user):
    """
    Генерирует PDF файл со списком покупок.

    Args:
        ingredients: Список ингредиентов с полями ingredient__name, 
                    ingredient__measurement_unit, и total_amount
        user: Объект пользователя

    Returns:
        FileResponse с PDF файлом для скачивания
    """

    buffer = io.BytesIO()

    font_path = os.path.join(os.path.dirname(__file__), 'Arial.ttf')
    font_name = 'Arial'
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception:
        font_name = 'Helvetica'  # fallback

    p = canvas.Canvas(buffer)
    p.setFont(font_name, 16)
    p.drawString(100, 750, f'Список покупок для {user.username}')
    p.setFont(font_name, 12)

    y = 700
    for i, item in enumerate(ingredients, 1):
        name = item['ingredient__name']
        unit = item['ingredient__measurement_unit']
        amount = item['total_amount']

        p.drawString(
            100, y, f'{i}. {name} - {amount} {unit}'
        )
        y -= 20

        if y <= 50:
            p.showPage()
            p.setFont(font_name, 12)
            y = 750

    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename='shopping_cart.pdf'
    )
