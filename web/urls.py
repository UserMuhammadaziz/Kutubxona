from django.urls import path, re_path

from . import views

urlpatterns = [
    # PWA service worker — IndexView catch-all'idan oldin turishi shart.
    path("sw.js", views.service_worker, name="service-worker"),
    # frontend React Router (BrowserRouter) ishlatadi: /books, /login kabi
    # yo'llar serverga so'rov bilan keladi va ularni SPA shell'ga
    # yo'naltirishimiz kerak. Bu view faqat "" ga xos bo'lsa, boshqa
    # barcha sahifalar 404 qaytarardi.
    re_path(r"^.*$", views.IndexView.as_view(), name="web-index"),
]
