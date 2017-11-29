from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'main/(?P<netid>[A-Za-z0-9_]+)/', views.main, name = 'main'),
    url(r'download/(?P<netid>[A-Za-z0-9_]+)/', views.download, name = 'download'),
    url(r'^logout/$', views.user_logout, name='logout'),
]
