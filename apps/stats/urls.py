from django.urls import path

from .views import (
    dashboard,
    faollik_reytingi,
    library_overall,
    library_ratings,
    my_ratings,
    rate_library,
    recent_activity,
    top_books,
    umummiy_bellashuv,
)

urlpatterns = [
    path("top-books/", top_books, name="stats-top-books"),
    path("recent-activity/", recent_activity, name="stats-recent-activity"),
    path("dashboard/", dashboard, name="stats-dashboard"),
    path("ratings/", library_ratings, name="stats-ratings"),
    path("ratings/overall/", library_overall, name="stats-ratings-overall"),
    path("ratings/activity/", faollik_reytingi, name="stats-ratings-activity"),
    path("ratings/competition/", umummiy_bellashuv, name="stats-ratings-competition"),
    path("ratings/me/", my_ratings, name="stats-ratings-me"),
    path("ratings/rate/", rate_library, name="stats-ratings-rate"),
]
