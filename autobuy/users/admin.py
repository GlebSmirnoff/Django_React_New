from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import EmailVerificationCode, PhoneVerificationCode, PasswordResetCode

User = get_user_model()

# Ensure no duplicate registration of User model
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model"""
    list_display = [
        'email', 'full_name', 'account_type', 'account_status', 'is_active', 'is_approved'
    ]
    list_filter = ['account_type', 'account_status', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'phone']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone', 'account_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved')}),
        ('Moderation', {'fields': ('account_status', 'moderator_notification_methods')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups', 'user_permissions',)

# Register User model with custom admin
admin.site.register(User, UserAdmin)

@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    """Admin for email verification codes"""
    list_display = ['user', 'code', 'created_at']
    readonly_fields = ['created_at']

@admin.register(PhoneVerificationCode)
class PhoneVerificationCodeAdmin(admin.ModelAdmin):
    """Admin for phone verification codes"""
    list_display = ['phone', 'code', 'created_at']
    readonly_fields = ['created_at']

@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    """Admin for password reset codes"""
    list_display = ['user', 'phone', 'code', 'via_sms', 'created_at']
    readonly_fields = ['created_at']

