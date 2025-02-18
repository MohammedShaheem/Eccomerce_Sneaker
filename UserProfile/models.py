from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver

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
    
 
class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('HOME','Home'),
        ('WORK','Work'),
        ('OTHER','Other'),
    ]
    
    
    #the basic fields
    name = models.CharField(max_length=100)
    house_name = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(
        max_length=6,
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message='Pincode must be 6 digits'
            )
        ]
    )
    
    email = models.EmailField()
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message='Phone number must be 10 digits'
    )
    
    phone = models.CharField(validators=[phone_regex], max_length=10)
    
    user = models.ForeignKey(get_user_model(),
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             null=True,
                             blank=True
                             )
    address_type = models.CharField(
        max_length=5,
        choices=ADDRESS_TYPE_CHOICES,
        default='HOME'    
    )
    
    is_default = models.BooleanField(default = False)
    
    
    
    landmark = models.CharField(max_length=50,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
    class Meta:
        db_table = 'Adress'
        ordering = ['-is_default','-created_at']
        
    def __str__(self):
        return f"{self.name}'s {self.address_type} Address"
    
    def save(self, *args, **kwargs):
        #checking if this is a new address it does not have a pk until it is saved to the database.
        is_new = self.pk is None
        
        if self.is_default:
            #setting all other addresses of this user to non default
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        
        elif is_new and not Address.objects.filter(user=self.user).exists():
            
            #setting default if:
                #it is a new address and no other addresses exist
                #no default address exists for thsi user
                
                self.is_default = True
        super().save(*args, **kwargs)

    @classmethod
    def set_default(cls, address_id,user):
        # settign an address as default and unsetting others
        
        try:
            address = cls.objects.get(id=address_id, user=user)
            address.is_default=True
            address.save()
            return True
        except cls.DoesNotExist:
            return False
        
    def delete(self, *args, **kwargs):
        #storing user references before deletion
        
        user = self.user
        was_default = self.is_default
        
        #performing deletion
        super().delete(*args, **kwargs)
        
        #if this was default address, set a new default
        if was_default:
            #get the most recently created address for this user
            new_default = Address.objects.filter(user=user).order_by('-created_at').first()
            if new_default:
                new_default.is_default  =  True
                new_default.save()

#signal handelr for when an address in deleted,ther will be an another defualt
@receiver(post_delete, sender=Address)
def set_new_default_address(sender, instance, **kwargs):
    if instance.is_default:
        #geting the user's remaining addresses
        remaining_addresses = Address.objects.filter(user=instance.user)
        if remaining_addresses.exists():
            #getting the most recent address and setting it as default
            new_default = remaining_addresses.order_by('-created_at').first()
            new_default.is_default = True
            new_default.save()
        

    
    