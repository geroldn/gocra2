from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='gocra-index'),
    path('current/', views.current, name='gocra-current'),
]
