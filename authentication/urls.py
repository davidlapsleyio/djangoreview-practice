from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("register/", views.RegistrationView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "token/refresh/",
        views.TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path("users/", views.UserListView.as_view(), name="user-list"),
]
