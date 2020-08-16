from django.urls import path
from . import views

urlpatterns = [
    path('', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('current/', views.current, name='gocra-current'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/', views.PlayerListView.as_view(), name='gocra-players'),
    path('series/', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('series_all/', views.SeriesListView.as_view(), name='gocra-series-list'),
    path('series_open/<int:id>/', views.series_open, name='gocra-series-open'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
]
