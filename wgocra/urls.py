from django.urls import path
from . import views

urlpatterns = [
    path('', views.SeriesDetailView.as_view(), name='gocra-series'),
    path('clubs/', views.ClubListView.as_view(), name='gocra-clubs'),
    path('players/<int:user>/', views.PlayerListView.as_view(), name='gocra-players'),
    path('add_player/<int:uid>/<int:plid>/', views.add_player, name='gocra-add-player'),
    path('add_account/', views.get_add_account, name='gocra-get_add-account'),
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
    path('new_series/', views.new_series, name='gocra-new-series'),
    path('upload/', views.upload_macmahon, name='gocra-upload'),
    path('add_round/<int:sid>/', views.add_round,
         name='gocra_add_round'),
    path('rem_round/<int:sid>/', views.rem_round,
         name='gocra_rem_round'),
    path('add_participant/<int:id>/', views.add_participant,
         name='gocra_add_participant'),
    path('add_participant_list/<int:id>/', views.add_active_participants,
         name='gocra_add_participant_list'),
    path('edit_participant/<int:pid>/', views.edit_participant,
         name='gocra_edit_participant'),
    path('del_participant/<int:pid>/', views.del_participant,
         name='gocra_del_participant'),
]
