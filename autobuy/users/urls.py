from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, ConfirmEmailView, LoginView, ProfileView, LogoutView,
    GoogleLoginAPIView, FacebookLoginView, AppleLoginAPIView,
    SendPhoneCodeView, RegisterByPhoneView,
    PasswordResetInitView, PasswordResetConfirmView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('register/confirm/', ConfirmEmailView.as_view(), name='auth_confirm_email'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('auth/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('auth/facebook/', FacebookLoginView.as_view(), name='facebook_login'),
    path('auth/apple/', AppleLoginAPIView.as_view(), name='apple_login'),
    path('phone/send-code/', SendPhoneCodeView.as_view(), name='send_phone_code'),
    path('phone/register/', RegisterByPhoneView.as_view(), name='register_by_phone'),
    path('reset-password/init/', PasswordResetInitView.as_view(), name='reset_password_init'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
]
