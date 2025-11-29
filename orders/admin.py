# orders/admin.py
from django.contrib import admin
from django.db import transaction
from django.contrib import messages

from .models import Order, OrderItem

# نضيف Action لـ Mark as Confirmed
def mark_as_confirmed(modeladmin, request, queryset):
    success = 0
    failed = 0
    for order in queryset:
        try:
            with transaction.atomic():
                if order.status in ('confirmed', 'fulfilled'):
                    continue  # إذا كانت الحالة Confirmed أو Fulfilled، لا نقوم بأي تغيير
                order.status = 'confirmed'  # نغيّر الحالة إلى "Confirmed"
                order.save()
                success += 1
        except Exception as e:
            failed += 1
            messages.error(request, f"Failed to confirm order {order.pk}: {e}")

    if success:
        messages.success(request, f"Successfully marked {success} orders as confirmed.")
    if failed:
        messages.error(request, f"{failed} orders failed to be confirmed.")

mark_as_confirmed.short_description = "Mark selected orders as Confirmed"

# نضيف Action لـ Mark as Fulfilled (خصم المخزون)
def mark_as_fulfilled(modeladmin, request, queryset):
    success = 0
    failed = 0
    for order in queryset:
        try:
            with transaction.atomic():
                if order.status == 'fulfilled':
                    continue  # إذا كانت الحالة Fulfilled، لا نقوم بأي تغيير
                order.status = 'fulfilled'  # نغيّر الحالة إلى "Fulfilled"
                order.save()  # سيتم خصم المخزون هنا باستخدام الـ signals
                success += 1
        except Exception as e:
            failed += 1
            messages.error(request, f"Failed to fulfill order {order.pk}: {e}")

    if success:
        messages.success(request, f"Successfully marked {success} orders as fulfilled.")
    if failed:
        messages.error(request, f"{failed} orders failed to be fulfilled.")

mark_as_fulfilled.short_description = "Mark selected orders as Fulfilled (deduct stock)"

# تعريف OrderItemInline لعرض العناصر داخل الطلب
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # لا حاجة لأسطر إضافية فارغة

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')  # عرض الحقول في الـ admin
    list_filter = ('status',)  # تصنيف الفلاتر حسب الحالة
    search_fields = ('user__email', 'status')  # البحث باستخدام البريد الإلكتروني أو الحالة
    inlines = [OrderItemInline]  # عرض عناصر الطلب بشكل مدمج
    actions = [mark_as_confirmed, mark_as_fulfilled]  # إضافة Actions جديدة

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price', 'created_at')
    search_fields = ('product__name',)
