from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'series', views.ImageSeriesViewSet, basename='series')
router.register(r'images', views.ImageUploadViewSet, basename='image')
router.register(r'annotations', views.AnnotationViewSet, basename='annotation')

urlpatterns = [
    path('', include(router.urls)),
]
