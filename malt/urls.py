from django.urls import path

from . import views


urlpatterns = [
    path('user/manage/', views.UserManageView.as_view(), name='user_manage'),
    path('user/edit/<int:pk>/', views.UserEditView.as_view(), name='user_edit'),
    path('user/remove/<int:pk>/', views.UserRemoveView.as_view(), name='user_remove'),
    path('user/promote/<int:pk>/', views.UserPromoteView.as_view(), name='user_promote'),
    path('user/demote/<int:pk>/', views.UserDemoteView.as_view(), name='user_demote'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('upload/code/', views.UploadCodeView.as_view(), name='upload_code'),
    path('upload/asset/public/', views.UploadAssetPublicView.as_view(), name='upload_asset_public'),
    path('upload/asset/private/', views.UploadAssetPrivateView.as_view(), name='upload_asset_private'),
    path('upload/asset/confirm/', views.UploadAssetConfirmView.as_view(), name='upload_asset_confirm'),
    path('', views.IndexView.as_view(), name='index'),
]
