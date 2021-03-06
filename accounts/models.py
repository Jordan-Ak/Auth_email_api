import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from accounts.managers import CustomUserManager
from common.models import BaseModel
from phonenumber_field.modelfields import PhoneNumberField
from accounts.tasks import generate_verification_token_sh

# Create your models here.
'''
Custom user model in which user data would be managed.
it deals exclusively with email, phone_no and name registration
'''

class CustomUser(AbstractUser, BaseModel):
    """
   Custom User Model
    """
    username = None
    date_joined = None
    first_name = models.CharField(_('first name'), max_length=150,)
    last_name = models.CharField(_('last name'), max_length=150,)
    email = models.EmailField(_('email address'), blank=False, unique = True)
    phone_no = PhoneNumberField(_('phone number'),unique = True,) 
    password_last_changed = models.DateTimeField(_('password last changed'), null=True)
    is_verified = models.BooleanField(_('is verified'), default = False,)
    
    email_verification_token = models.CharField(_('Email Verification Token'), max_length =255 ,
                                                unique = True, null = True,)
    email_token_sent_at = models.DateTimeField(_('Email Token Sent at'),null = True)

    password_reset_token = models.CharField(_('Password Reset Token'), max_length = 255,
                                                unique = True, null = True,)
    
    password_reset_sent_at = models.DateTimeField(_('Password Reset Sent at'), null = True,)
    #Forgot to add a try incase verification token produces same token twice

    def generate_email_verification_token(self) -> None:
        #self.email_verification_token = secrets.token_urlsafe(50)
        self.email_token_sent_at = timezone.now()
        self.email_verification_token = generate_verification_token_sh.apply_async().get() #both functions at the end enable celery return json data
        self.save()

    def has_email_verification_token_expired(self) -> bool:
        return self.email_token_sent_at > self.email_token_sent_at + timedelta(hours=24)

    def confirm_email(self) -> None:
        self.email_verification_token = None
        self.email_token_sent_at = None
        self.is_verified = True
        self.save()

    def generate_password_reset_token(self) -> None:
        self.password_reset_token = generate_verification_token_sh.apply_async().get()
        self.password_reset_sent_at = timezone.now()
        self.save()
    
    def has_password_reset_token_expired(self) -> bool:
        return self.password_reset_sent_at > self.password_reset_sent_at + timedelta(hours=24)

    def confirm_reset(self) -> None:
        self.password_reset_token = None
        self.password_reset_sent_at = None
        self.save()

    
    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name','phone_no',]

    def __str__(self) -> str:
        return self.email



