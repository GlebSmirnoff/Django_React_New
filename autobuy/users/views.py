import random
from django.conf import settings
from django.core.signing import TimestampSigner
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import User, EmailVerificationCode, PhoneVerificationCode, PasswordResetCode
from .serializers import (
    RegisterSerializer,
    ConfirmEmailSerializer,
    LoginSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    SendPhoneCodeSerializer,
    RegisterByPhoneSerializer,
    PasswordResetInitSerializer,
    PasswordResetConfirmSerializer,
)

signer = TimestampSigner()
User = get_user_model()

# Helper: notify moderator of new pending user
def notify_moderator(user):
    methods = user.moderator_notification_methods or []
    msg = f"Нова заявка на модерацію: {user.email} ({user.get_account_type_display()})"
    # Mock notifications
    if 'email' in methods:
        print(f"✉️ Email to moderator: {msg}")
    if 'sms' in methods:
        print(f"📱 SMS to moderator: {msg}")
    if 'telegram' in methods:
        print(f"💬 Telegram to moderator: {msg}")

class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            code = str(random.randint(100000, 999999))
            EmailVerificationCode.objects.create(user=user, code=code)
            print(f"📧 Email confirmation for {user.email}: {code}")
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmEmailView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ConfirmEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # activate user
            user.is_active = True
            # auto-approve buyers
            if user.account_type == 'buyer':
                user.account_status = 'approved'
                user.is_approved = True
            else:
                user.account_status = 'pending'
                user.is_approved = False
                notify_moderator(user)
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            # only allow login if approved
            if not user.is_active or not user.is_approved:
                return Response({'detail': 'User not approved yet'}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        id_token_from_client = request.data.get('id_token')
        if not id_token_from_client:
            return Response({'error': 'Missing id_token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_from_client,
                google_requests.Request(),
                settings.SOCIAL_GOOGLE_CLIENT_ID
            )
            email = idinfo['email']
            full_name = idinfo.get('name', '')
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'full_name': full_name, 'is_active': True, 'is_approved': True, 'account_status': 'approved'}
            )
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Invalid Google token: {e}'}, status=status.HTTP_400_BAD_REQUEST)

class FacebookLoginView(APIView):
    permission_classes = []

    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response({'error': 'Access token is required'}, status=status.HTTP_400_BAD_REQUEST)
        debug_url = (
            f'https://graph.facebook.com/debug_token?'
            f'input_token={access_token}&'
            f'access_token={settings.SOCIAL_FACEBOOK_APP_ID}|{settings.SOCIAL_FACEBOOK_APP_SECRET}'
        )
        debug_res = requests.get(debug_url).json()
        if not debug_res.get('data', {}).get('is_valid'):
            return Response({'error': 'Invalid Facebook token'}, status=status.HTTP_400_BAD_REQUEST)
        profile_url = f'https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}'
        fb_data = requests.get(profile_url).json()
        email = fb_data.get('email')
        full_name = fb_data.get('name', '')
        if not email:
            return Response({'error': 'Email not provided by Facebook'}, status=status.HTTP_400_BAD_REQUEST)
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'full_name': full_name, 'is_active': True, 'is_approved': True, 'account_status': 'approved'}
        )
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)

class AppleLoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'Missing id_token'}, status=status.HTTP_400_BAD_REQUEST)
        # mock verification or real depending on setup
        email = f'apple_user_{requests.utils.quote(token)[:8]}@apple.fake'
        full_name = 'Apple User'
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'full_name': full_name, 'is_active': True, 'is_approved': True, 'account_status': 'approved'}
        )
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)

class SendPhoneCodeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SendPhoneCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            code = str(random.randint(100000, 999999))
            PhoneVerificationCode.objects.create(phone=phone, code=code)
            print(f"🔐 SMS-код для {phone}: {code}")
            return Response({'detail': 'Код надіслано'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterByPhoneView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterByPhoneSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user.account_type != 'buyer':
                notify_moderator(user)
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetInitView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetInitSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            return Response({'detail': 'Reset initiated'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password changed'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

