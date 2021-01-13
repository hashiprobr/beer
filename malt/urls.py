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
    path('move/assets/<path:path>/', views.AssetMoveView.as_view(), name='asset_move'),
    path('move/file/assets/<path:path>', views.AssetMoveFileView.as_view(), name='asset_move_file'),
    path('trash/assets/<path:path>/', views.AssetTrashView.as_view(), name='asset_trash'),
    path('trash/file/assets/<path:path>', views.AssetTrashFileView.as_view(), name='asset_trash_file'),
    path('recycle/', views.AssetRecycleView.as_view(), name='asset_recycle'),
    path('restore/assets/<int:pk>/', views.AssetRestoreView.as_view(), name='asset_restore'),
    path('restore/file/assets/<int:pk>/', views.AssetRestoreFileView.as_view(), name='asset_restore_file'),
    path('remove/assets/<int:pk>/', views.AssetRemoveView.as_view(), name='asset_remove'),
    path('remove/file/assets/<int:pk>', views.AssetRemoveFileView.as_view(), name='asset_remove_file'),
    path('calendar/<str:user>/<slug:slug>/', views.CalendarView.as_view(), name='calendar'),
    path('draft/calendar/<str:user>/<slug:slug>/', views.CalendarView.as_view(), name='calendar_draft'),
    path('move/calendar/<str:user>/<slug:slug>/', views.CalendarMoveView.as_view(), name='calendar_move'),
    path('move/draft/calendar/<str:user>/<slug:slug>/', views.CalendarMoveView.as_view(), name='calendar_move_draft'),
    path('remove/calendar/<str:user>/<slug:slug>/', views.CalendarRemoveView.as_view(), name='calendar_remove'),
    path('remove/draft/calendar/<str:user>/<slug:slug>/', views.CalendarRemoveView.as_view(), name='calendar_remove_draft'),
    path('publish/draft/calendar/<str:user>/<slug:slug>/', views.CalendarPublishView.as_view(), name='calendar_publish_draft'),
    path('', views.IndexView.as_view(), name='index'),
]
