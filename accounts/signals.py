# accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile
from orders.models import Order
from decimal import Decimal

User = settings.AUTH_USER_MODEL

# Create profile when new user created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

# cache previous order status to detect changes
_prev_order_status = {}

@receiver(pre_save, sender=Order)
def cache_prev_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            prev = Order.objects.get(pk=instance.pk)
            _prev_order_status[instance.pk] = prev.status
        except Order.DoesNotExist:
            _prev_order_status[instance.pk] = None

@receiver(post_save, sender=Order)
def update_profile_on_order_change(sender, instance, created, **kwargs):
    """
    عند إنشاء طلب جديد نحدث إجمالي الـ profile.
    عند تغيير حالة الطلب (مثلاً إلى 'cancelled') يمكن تعديل القيم إن رغبت.
    """
    user = getattr(instance, 'user', None)
    if not user:
        return

    profile, _ = Profile.objects.get_or_create(user=user)

    # safety for total
    order_total = getattr(instance, 'total', None) or Decimal('0.00')

    if created:
        # update stats on create
        profile.orders_count = profile.orders_count + 1
        profile.total_spent = (profile.total_spent or Decimal('0.00')) + Decimal(order_total)
        profile.last_order_date = getattr(instance, 'created_at', None) or getattr(instance, 'updated_at', None)
        profile.save()
        return

    # handle status change
    prev_status = _prev_order_status.pop(instance.pk, None)
    new_status = getattr(instance, 'status', None)

    if prev_status != new_status:
        # example logic:
        # if order was previously not cancelled and now cancelled => deduct
        if prev_status != 'cancelled' and new_status == 'cancelled':
            profile.orders_count = max(0, profile.orders_count - 1)
            profile.total_spent = max(0, profile.total_spent - Decimal(order_total))
            profile.save()
        # if order moved from cancelled to delivered/active => add back (depends on your policy)
        # if prev_status == 'cancelled' and new_status in ['delivered','completed']:
        #     profile.orders_count = profile.orders_count + 1
        #     profile.total_spent = profile.total_spent + Decimal(order_total)
        #     profile.save()
