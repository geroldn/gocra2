from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='gocra-index'),
    path('current/', views.current, name='gocra-current'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/', views.PlayerListView.as_view(), name='gocra-players'),
    path('series/', views.series, name='gocra-series'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
]
