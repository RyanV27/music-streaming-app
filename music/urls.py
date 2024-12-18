from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name = 'index'),
    path('login',views.login,name = 'login'),
    path('signup',views.signup,name = 'signup'),
    path('logout',views.logout,name = 'logout'),
    path('upload',views.upload,name = 'upload'),
    path('music',views.music,name = 'music'),
    path('songs', views.songs_view, name='songs_list'),
    path('history', views.listening_history, name='listening_history'),
    path('notify_song_click/', views.notify_song_click, name='notify_song_click'),
    path('playlists', views.list_playlists, name='playlists'),
    path('playlists/create', views.create_playlist, name='create_playlist'),
    path('playlists/delete', views.delete_playlist, name='delete_playlist'),
    path('playlists/<str:playlist_name>/', views.list_playlist_songs, name='list_playlist_songs'),
    path('playlists/<str:playlist_name>/remove_song/', views.remove_playlist_song, name='remove_playlist_song'),
    path('playlists/<str:playlist_name>/add_song/', views.add_playlist_song, name='add_playlist_song'),
    path('playlists/<str:playlist_name>/remove_song/', views.remove_playlist_song, name='remove_playlist_song'),
    #path('upload_success', views.upload_success, name='upload_success'),
]