from django.urls import path
from . import views

urlpatterns = [
    path('<int:recipe_id>/', views.redirect_recipe, name='recipe_redirect'),

]