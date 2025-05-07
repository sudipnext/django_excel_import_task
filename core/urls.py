from rest_framework.routers import DefaultRouter
from .views import index, FileUploadViewSet, LogsViewSet, AnalyticsViewSet
from django.urls import path, include
router = DefaultRouter()

router.register(r'upload', FileUploadViewSet, basename='upload')
router.register(r'logs', LogsViewSet, basename='logs')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', index, name='index')

]
