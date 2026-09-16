from rest_framework import viewsets

from .models import User
from .permissions import IsAdmin
from .serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    GET   /api/staff/       -> xodimlar ro'yxati (faqat administrator)
    POST  /api/staff/       -> yangi kutubxonachi akkaunti yaratish
    GET   /api/staff/{id}/  -> bitta xodim
    PATCH /api/staff/{id}/  -> tahrirlash (masalan is_active=False qilish)
    Xodim hech qachon DELETE bilan o'chirilmaydi — faqat is_active=False.
    """

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer
