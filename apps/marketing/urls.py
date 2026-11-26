from django.urls import path

from . import views

urlpatterns = [
    path("visit/", views.track_visit),
    path("report/", views.marketing_report),
]
