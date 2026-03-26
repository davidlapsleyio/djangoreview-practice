from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("admin/", views.AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/<int:pk>/delete/", views.AdminUserDeleteView.as_view(), name="admin-user-delete"),
    path("admin/<int:pk>/reset-password/", views.admin_reset_password, name="admin-reset-password"),
    path("<int:pk>/orders/", views.user_order_history, name="user-order-history"),
]
