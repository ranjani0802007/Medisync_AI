from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.me),
    path("register/", views.register),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("demo/", views.demo),
    path("state/", views.state),
    path("sync/", views.sync),
]
