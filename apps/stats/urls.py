from django.urls import path

from . import views

urlpatterns = [
    path("top-books/", views.top_books, name="stats-top-books"),
    path("dashboard/", views.dashboard, name="stats-dashboard"),
]
