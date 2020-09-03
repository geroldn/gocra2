from django.urls import path
from . import views

urlpatterns = [
    path('', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/', views.PlayerListView.as_view(), name='gocra-players'),
    path('series/', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('round/<int:current>', views.RoundDetailView.as_view(), name='gocra-round'),
    path('add_game/<int:p_id>/<int:current>/', views.add_game,
         name='gocra-add-game'),
    path('wins_game/<int:r_id>/<str:color>/', views.wins_game,
         name='gocra-add-game'),
    path('make_pairing/<int:current>/', views.make_pairing,
         name='gocra-make-pairing'),
    path('drop_pairing/<int:current>/', views.drop_pairing,
         name='gocra-drop-pairing'),
    path('series_all/', views.SeriesListView.as_view(), name='gocra-series-list'),
    path('series_set_round/<int:round>/', views.series_set_round, name='gocra-series-set_round'),
    path('series_open/<int:id>/', views.series_open, name='gocra-series-open'),
    path('series_delete/<int:id>/', views.series_delete, name='gocra-series-delete'),
    path('toggle_playing_user/<int:sid>/<int:uid>/', views.toggle_playing_user,
         name='gocra-result-toggle-playing'),
    path('result_toggle_playing/<int:id>/', views.result_toggle_playing,
         name='gocra-result-toggle-playing'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
]
