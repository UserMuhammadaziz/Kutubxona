from django.urls import re_path

from . import views

urlpatterns = [
    # frontend React Router (BrowserRouter) ishlatadi: /books, /login kabi
    # yo'llar serverga so'rov bilan keladi va ularni SPA shell'ga
    # yo'naltirishimiz kerak. Bu view faqat "" ga xos bo'lsa, boshqa
    # barcha sahifalar 404 qaytarardi.
    re_path(r"^.*$", views.IndexView.as_view(), name="web-index"),
]
