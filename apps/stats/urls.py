from django.urls import path

from .views import (
    dashboard,
    faollik_reytingi,
    library_overall,
    library_ratings,
    my_ratings,
    rate_library,
    top_books,
    umummiy_bellashuv,
)

urlpatterns = [
    path("top-books/", top_books, name="stats-top-books"),
    path("dashboard/", dashboard),
    path("ratings/", library_ratings),
    path("ratings/overall/", library_overall),
    path("ratings/activity/", faollik_reytingi),
    path("ratings/competition/", umummiy_bellashuv),
    path("ratings/me/", my_ratings),
    path("ratings/rate/", rate_library),
]
