from django.urls import path, re_path

from . import views

urlpatterns = [
    # PWA service worker — IndexView catch-all'idan oldin turishi shart.
    path("sw.js", views.service_worker, name="service-worker"),
    # Uploaded organization logos (must stay before the public-file pattern).
    path("media/logos/<str:name>", views.media_logo, name="media-logo"),
    # Root files of the frontend build (logo, landing screenshots, manifest).
    # A path that looks like a file must never fall through to the SPA shell.
    re_path(
        r"^(?P<path>(?:[\w.-]+/)*[\w.-]+\.(?:png|jpe?g|webp|svg|ico|json|webmanifest|txt|xml))$",
        views.public_file,
        name="public-file",
    ),
    # Chatbot API endpoint
    path("api/chatbot/", views.ChatbotView.as_view(), name="chatbot"),
    path("api/ai/librarian-command/", views.LibrarianCommandView.as_view(), name="librarian-command"),
    # frontend React Router (BrowserRouter) ishlatadi: /books, /login kabi
    # yo'llar serverga so'rov bilan keladi va ularni SPA shell'ga
    # yo'naltirishimiz kerak. Bu view faqat "" ga xos bo'lsa, boshqa
    # barcha sahifalar 404 qaytarardi.
    re_path(r"^.*$", views.IndexView.as_view(), name="web-index"),
]
