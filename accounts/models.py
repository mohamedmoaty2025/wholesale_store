from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

# لا تغير قيمة AUTH_USER_MODEL هنا؛ استخدم settings.AUTH_USER_MODEL كـ string في العلاقات
# (أو استخدم get_user_model() عند الحاجة في أماكن أخرى)
# User = settings.AUTH_USER_MODEL  # يمكنك إبقاؤها إذا تستخدمها، لكن تجنب إعادة تعريفها لاحقاً


class Profile(models.Model):
    VIP_CHOICES = (
        ('normal','Normal'),
        ('vip','VIP'),
        ('wholesale','Wholesale'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    orders_count = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    vip_status = models.CharField(max_length=20, choices=VIP_CHOICES, default='normal')
    note = models.TextField(blank=True, default='')

    # ✅ الحقول الجديدة
    number_phone = models.CharField(max_length=30, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    address = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f'{getattr(self.user, "username", str(self.user))} profile'


# optional: PriceGroup unchanged
class PriceGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# User custom (keep as is)
class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='accounts_users',
        related_query_name='accounts_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='accounts_user_permissions',
        related_query_name='accounts_user_permission'
    )
    company_name = models.CharField(max_length=255, blank=True)
    is_wholsale = models.BooleanField(default=False)
    price_group = models.ForeignKey(PriceGroup, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.username}-{self.email}"


# ---------------------------
# signal لإنشاء Profile آليًا
# ---------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # إذا لم يُنشَأ Profile من مكان آخر فأنشئه هنا
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    # هذا يضمن حفظ البروفايل عند حفظ المستخدم لاحقًا (اختياري)
    if hasattr(instance, 'profile'):
        instance.profile.save()
