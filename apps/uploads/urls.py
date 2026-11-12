from django.urls import path
from .views import UploadCreateView, UploadListView, UploadDetailView

urlpatterns = [
    path('', UploadListView.as_view(), name='upload-list'),
    path('create/', UploadCreateView.as_view(), name='upload-create'),
    path('<uuid:pk>/', UploadDetailView.as_view(), name='upload-detail'),
]
