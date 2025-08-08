from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import datetime


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, account_type='buyer', **extra_fields):
        if not email:
            raise ValueError("Користувач повинен мати email")
        email = self.normalize_email(email)
        # за замовчуванням статус pending для нових користувачів
        user = self.model(
            email=email,
            account_type=account_type,
            account_status='pending',
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("account_status", "approved")
        return self.create_user(email, password, account_type='admin', **extra_fields)


ACCOUNT_TYPES = [
    ("buyer", "Покупець/Продавець"),
    ("service", "СТО"),
    ("parts", "Запчастини"),
    ("rental", "Прокат"),
    ("insurance", "Страхування"),
    ("dealer", "Автосалон"),
    ("admin", "Адміністратор"),
]

ACCOUNT_STATUS = [
    ("pending", "На розгляді"),
    ("approved", "Схвалено"),
    ("rejected", "Відхилено"),
]

NOTIFICATION_METHODS = [
    ("email", "Email"),
    ("telegram", "Telegram"),
    ("sms", "SMS"),
]


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default="buyer",
        help_text="Тип аккаунта"
    )
    # статус модерації
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS,
        default="pending",
        help_text="Статус модерації"
    )
    # Методи оповіщення модератора
    moderator_notification_methods = models.JSONField(
        default=list,
        blank=True,
        help_text="Список методів оповіщення модератора"
    )

    is_active = models.BooleanField(default=False)  # активується після підтвердження пошти
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)  # додаткова позначка

    created_at = models.DateTimeField(auto_now_add=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone"]

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.get_account_type_display()})"


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.email} → {self.code}"


class PhoneVerificationCode(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=3)

    def __str__(self):
        return f'{self.phone} - {self.code}'


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    code = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    via_sms = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=10)

    def __str__(self):
        target = self.user.email if self.user else self.phone
        return f"Password reset for {target}"


