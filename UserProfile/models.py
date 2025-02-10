from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import random

# Create your models here.
class UserTable(AbstractUser):
    Phone_number = models.CharField(max_length=50, unique=True, null=False, blank=False)
    gender = models.CharField(max_length=50)
    is_blocked = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default = False)
    email_otp = models.CharField(max_length=6, null=True,blank=True)
    email = models.EmailField(unique=True)
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='Custom_user_permissions',
        blank=True
    )
    
   

    class Meta:
        db_table = 'UserTable'

    def __str__(self):
        return self.username
    
 