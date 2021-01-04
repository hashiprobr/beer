from django.urls import path

from . import views


urlpatterns = [
    path('user/', views.UserManageView.as_view(), name='user_manage'),
    path('user/add/', views.UserAddView.as_view(), name='user_add'),
    path('user/edit/<int:pk>/', views.UserEditView.as_view(), name='user_edit'),
    path('user/remove/<int:pk>/', views.UserRemoveView.as_view(), name='user_remove'),
    path('user/promote/<int:pk>/', views.UserPromoteView.as_view(), name='user_promote'),
    path('user/demote/<int:pk>/', views.UserDemoteView.as_view(), name='user_demote'),
    path('upload/', views.UploadManageView.as_view(), name='upload_manage'),
    path('upload/code/', views.UploadCodeView.as_view(), name='upload_code'),
    path('upload/asset/', views.UploadAssetView.as_view(), name='upload_asset'),
    path('upload/asset/confirm/', views.UploadAssetConfirmView.as_view(), name='upload_asset_confirm'),
    path('assets/', views.AssetManageView.as_view(), {'path': ''}, name='asset_manage'),
    path('assets/<path:path>/', views.AssetManageView.as_view(), name='asset_manage_folder'),
    path('edit/assets/<path:path>/', views.AssetEditView.as_view(), name='asset_edit'),
    path('edit/file/assets/<path:path>', views.AssetEditFileView.as_view(), name='asset_edit_file'),
    path('remove/assets/<path:path>/', views.AssetRemoveView.as_view(), name='asset_remove'),
    path('remove/file/assets/<path:path>', views.AssetRemoveFileView.as_view(), name='asset_remove_file'),
    path('', views.IndexView.as_view(), name='index'),
    path('calendar/<str:username>/<slug:slug>/', views.CalendarView.as_view(), name='calendar'),
    path('draft/calendar/<str:username>/<slug:slug>/', views.CalendarView.as_view(), name='calendar_draft'),
]
