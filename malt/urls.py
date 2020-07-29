from django.urls import path

from . import views


urlpatterns = [
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('upload/code/', views.UploadCodeView.as_view(), name='upload_code'),
    path('upload/asset/public/', views.UploadAssetPublicView.as_view(), name='upload_asset_public'),
    path('upload/asset/private/', views.UploadAssetPrivateView.as_view(), name='upload_asset_private'),
    path('upload/asset/confirm/', views.UploadAssetConfirmView.as_view(), name='upload_asset_confirm'),
    path('', views.IndexView.as_view(), name='index'),
]
