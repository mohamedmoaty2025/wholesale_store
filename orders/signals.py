# orders/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from orders.models import Order
from catalog.models import Product  # عدل المسار لو الموديل في مكان آخر
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Order)
def deduct_stock_on_fulfill(sender, instance: Order, **kwargs):
    """
    قبل حفظ Order جديد/مُحدّث: إذا الحالة اتبدلت لـ 'fulfilled' من حالة تانية،
    نقص من كل منتج الكمية المطلوبة.
    نستخدم pre_save لمقارنة الحالة الحالية بالحالة في DB قبل التحديث.
    """
    if not instance.pk:
        # طلب جديد، لا نخصم هنا لأن الحالة عادة تكون 'pending' عند الإنشاء
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    prev_status = previous.status
    new_status = instance.status

    # نتحقق إن الحالة تغيّرت إلى fulfilled
    if prev_status != 'fulfilled' and new_status == 'fulfilled':
        # نعمل العملية داخل transaction.atomic لضمان الاتساق
        with transaction.atomic():
            for item in instance.items.all():
                product = item.product
                qty = item.quantity or 0
                # احسب الجديدة ولا تسمح بالعدد السالب
                new_stock = (product.stock or 0) - qty
                if new_stock < 0:
                    # اختياري: هنا نمنع السالب ونجعلها صفر
                    logger.warning("Order %s: product %s stock would go negative (%s). Setting to 0.",
                                   instance.pk, product.pk, new_stock)
                    new_stock = 0
                # حدّث الحقل
                product.stock = new_stock
                product.save(update_fields=['stock'])
            logger.info("Order %s fulfilled: stock deducted.", instance.pk)
