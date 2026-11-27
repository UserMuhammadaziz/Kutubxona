from django.urls import path

from .views import BotReviewView, ReviewHideView, ReviewListView

urlpatterns = [
    path("", ReviewListView.as_view()),
    path("<int:pk>/hide/", ReviewHideView.as_view()),
    path("bot/", BotReviewView.as_view()),
]
