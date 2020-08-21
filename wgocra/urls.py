from django.urls import path
from . import views

urlpatterns = [
    path('', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('current/', views.current, name='gocra-current'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/', views.PlayerListView.as_view(), name='gocra-players'),
    path('series/', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('round/<int:id>', views.RoundDetailView.as_view(), name='gocra-round'),
    path('series_all/', views.SeriesListView.as_view(), name='gocra-series-list'),
    path('series_set_round/<int:round>/', views.series_set_round, name='gocra-series-set_round'),
    path('series_open/<int:id>/', views.series_open, name='gocra-series-open'),
    path('series_delete/<int:id>/', views.series_delete, name='gocra-series-delete'),
    path('result_toggle_playing/<int:id>/', views.result_toggle_playing,
         name='gocra-result-toggle-playing'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
]
