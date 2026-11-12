from rest_framework.routers import DefaultRouter

from .views import OrganizationViewSet, SaaSOrganizationViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organizations")
router.register("saas/organizations", SaaSOrganizationViewSet, basename="saas-organizations")
urlpatterns = router.urls
