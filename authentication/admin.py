from django.contrib import admin

from .models import PasswordResetToken, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "login_count", "last_login_ip"]
    search_fields = ["user__username", "user__email"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token", "created_at"]
    search_fields = ["user__email"]
