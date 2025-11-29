#نستورد ادوات التعريف الحقول والموديلات مثل charfiled
from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models  import AbstractUser
from django.utils.translation import gettext_lazy as _
User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    VIP_CHOICES = (
        ('normal','Normal'),
        ('vip','VIP'),
        ('wholesale','Wholesale'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    orders_count = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    vip_status = models.CharField(max_length=20, choices=VIP_CHOICES, default='normal')
    note = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f'{getattr(self.user, "username", str(self.user))} profile'
 #موديل يخزن اسم ووصف كل مجموعه سعر
class PriceGroup(models.Model):
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    


#موديل المستخدم المخصص يرث كل الخصائص من Abstractuser
class User(AbstractUser):
    groups = models.ManyToManyField('auth.Group',verbose_name=_('groups'),blank=True, help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),related_name='accounts_users',related_query_name='accounts_user')
    user_permissions = models.ManyToManyField('auth.Permission',verbose_name=_('user permissions'),blank=True, help_text=_('Specific permissions for this user.'), related_name='accounts_user_permissions', related_query_name='accounts_user_permission')
    company_name = models.CharField(max_length=255,blank=True)#حقل نصى لاسم الشركه او التأجر
    is_wholsale = models.BooleanField(default=False) #لتحديد هل الحساب لتاجر او لا
    price_group = models.ForeignKey(PriceGroup,null=True,blank=True,on_delete=models.SET_NULL) 
    
    def __str__(self):
        return f"{self.username}-{self.email}"
    
    


