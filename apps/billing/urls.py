from django.urls import path

from .views import checkout, overview, payment_detail

urlpatterns = [
    path("", overview, name="billing-overview"),
    path("checkout/", checkout, name="billing-checkout"),
    path("payments/<int:pk>/", payment_detail, name="billing-payment"),
]
