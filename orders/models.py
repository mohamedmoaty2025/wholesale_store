# orders/models.py
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from catalog.models import Product

class Order(models.Model):
    """
    نموذج الطلب الرئيسي.
    يحتوي على بيانات العميل، الحالة، الاجمالي، وتاريخ الانشاء.
    """
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_FULFILLED = 'fulfilled'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_FULFILLED, 'Fulfilled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    # بيانات العميل
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_city = models.CharField(max_length=200, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.status}"

    def recalc_total(self):
        """
        يحسب مجموع السعر بناءً على OrderItem المرتبطة بهذا الطلب.
        يعيد الـ total كـ Decimal ويحدّث الحقل في DB.
        """
        items = self.items.all()
        total = Decimal('0.00')
        for it in items:
            total += (it.unit_price * it.quantity)
        self.total = total
        self.save(update_fields=['total'])
        return self.total

    def save(self, *args, **kwargs):
        """
        نعدل الحقول الخاصة بالعميل لتأخذ بياناته من الـ request.user إذا كان مسجلاً.
        """
        if self.user:
            if not self.customer_name:
                self.customer_name = f"{self.user.first_name} {self.user.last_name}"
            if not self.customer_phone:
                self.customer_phone = self.user.profile.mobile if self.user.profile else ''
            if not self.customer_email:
                self.customer_email = self.user.email
            if not self.customer_address:
                self.customer_address = self.user.profile.address if self.user.profile else ''
            if not self.customer_city:
                self.customer_city = self.user.profile.city if self.user.profile else ''

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    عنصر واحد داخل الطلب: ربط لمنتج مع الكمية والسعر عند الشراء.
    نخزن unit_price ثابت عند وقت الشراء (حتى لو تغير سعر المنتج بعدين).
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)  # السعر لكل وحدة عند وقت الطلب
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            sku = self.product.sku
        except Exception:
            sku = str(self.product_id)
        return f"{sku} x {self.quantity} @ {self.unit_price}"
