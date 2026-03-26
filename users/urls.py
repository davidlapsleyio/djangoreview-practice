from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
]
