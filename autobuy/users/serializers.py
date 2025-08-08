from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.utils.crypto import get_random_string
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from .models import (
    User,
    EmailVerificationCode,
    PhoneVerificationCode,
    PasswordResetCode,
)

signer = TimestampSigner()
User = get_user_model()


# 1. Реєстрація через email
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'account_type', 'password']

    def validate(self, data):
        if not data.get('phone'):
            raise serializers.ValidationError({"phone": "Це поле необхідно заповнити"})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
            account_type=validated_data.get('account_type', 'buyer'),
            is_active=False,
            is_approved=(validated_data.get('account_type') == 'buyer')
        )
        return user


# 2. Підтвердження email‑коду
class ConfirmEmailSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        try:
            record = EmailVerificationCode.objects.filter(code=value).latest('created_at')
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("Невірний або прострочений код підтвердження")
        if record.is_expired():
            raise serializers.ValidationError("Код підтвердження прострочено")
        self.context['record'] = record
        return value

    def save(self, **kwargs):
        record = self.context['record']
        user = record.user
        user.is_active = True
        # автоматично схвалити, якщо buyer
        if user.account_type == 'buyer':
            user.is_approved = True
            user.account_status = 'approved'
        user.save()
        EmailVerificationCode.objects.filter(user=user).delete()
        return user


# 3. Логін
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Невірний email або пароль.")


# 4. Вивід профілю
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'account_type', 'phone', 'account_status', 'created_at']


# 4b. Оновлення профілю
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'account_type']


# 5. Ініціація SMS
class SendPhoneCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


# 6. Реєстрація через телефон
class RegisterByPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)
    full_name = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            record = PhoneVerificationCode.objects.filter(
                phone=data['phone'], code=data['code']
            ).latest('created_at')
        except PhoneVerificationCode.DoesNotExist:
            raise serializers.ValidationError("Невірний або прострочений код")
        if record.is_expired():
            raise serializers.ValidationError("Код прострочено")
        return data

    def create(self, validated_data):
        random_password = get_random_string(12)
        user = User.objects.create_user(
            email=f"{validated_data['phone']}@sms.fake",
            full_name=validated_data['full_name'],
            password=random_password,
            phone=validated_data['phone'],
            is_active=True,
            is_approved=True,
            account_status='approved'
        )
        return user


# 7. Ініціація скидання паролю
class PasswordResetInitSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Потрібно вказати email або номер телефону.")
        return data


# 8. Підтвердження скидання паролю
class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(required=False)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        token = attrs.get("token")
        phone = attrs.get("phone")
        code = attrs.get("code")

        if token:
            try:
                user_id = signer.unsign(token, max_age=600)
                user = User.objects.get(pk=user_id)
                attrs["user"] = user
            except (BadSignature, SignatureExpired, User.DoesNotExist):
                raise serializers.ValidationError("Недійсний або прострочений токен.")
        elif phone and code:
            try:
                record = PasswordResetCode.objects.filter(
                    phone=phone, code=code
                ).latest('created_at')
            except PasswordResetCode.DoesNotExist:
                raise serializers.ValidationError("Код недійсний або прострочений.")
            if record.is_expired():
                raise serializers.ValidationError("Код прострочено.")
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                raise serializers.ValidationError("Користувача не знайдено.")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("Потрібно вказати або токен, або телефон і код.")

        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
