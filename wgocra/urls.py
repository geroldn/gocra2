from django.urls import path
from . import views

urlpatterns = [
    path('', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/', views.PlayerListView.as_view(), name='gocra-players'),
    path('series/', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('round/<int:current>', views.RoundDetailView.as_view(), name='gocra-round'),
    path('add_game/<int:p_id>/<int:current>/<int:game>/', views.add_game,
         name='gocra-add-game'),
    path('del_game/<int:r_id>/', views.del_game,
         name='gocra-del-game'),
    path('wins_game/<int:r_id>/<str:color>/', views.wins_game,
         name='gocra-wins-game'),
    path('make_pairing/<int:current>/', views.make_pairing,
         name='gocra-make-pairing'),
    path('drop_pairing/<int:current>/', views.drop_pairing,
         name='gocra-drop-pairing'),
    path('series_all/', views.SeriesListView.as_view(), name='gocra-series-list'),
    path('series_set_round/<int:round>/', views.series_set_round,
         name='gocra-series-set_round'),
    path('series_open/<int:id>/', views.series_open, name='gocra-series-open'),
    path('series_finalize/<int:id>/', views.series_finalize,
         name='gocra-series-finalize'),
    path('series_delete/<int:id>/', views.series_delete, name='gocra-series-delete'),
    path('user_result/<int:sid>/<int:win>/<int:round>/', views.user_result,
         name='gocra-user-result'),
    path('set_playing_user/<int:sid>/<int:playing>/', views.set_playing_user,
         name='gocra-result-set-playing'),
    path('result_set_playing/<int:id>/<int:playing>/', views.result_set_playing,
         name='gocra-result-set-playing'),
    path('club_select/<int:id>/', views.club_select, name='gocra-club-select'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
    path('add_participant/<int:id>/', views.add_participant,
         name='gocra_add_participant'),
    path('del_participant/<int:pid>/', views.del_participant,
         name='gocra_del_participant'),
]
