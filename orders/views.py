# orders/views.py
from decimal import Decimal
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import logging

from .models import Order, OrderItem
from catalog.models import Product
from .serializers import CreateOrderSerializer, OrderReadSerializer  # تأكد أن هذه الأسماء موجودة في serializers.py

# Google sheets helper
from utils.google_sheets import append_order_to_sheet

logger = logging.getLogger(__name__)

class CreateOrderView(APIView):
    """
    POST /api/orders/create/
    يتوقع JSON بالشكل:
    {
      "customer_name":"...",
      "customer_phone":"...",
      "customer_email":"...",
      "customer_city":"...",
      "customer_address":"...",
      "items": [{"product_id":1, "quantity": 10}, ...]
    }
    يقوم بإنشاء Order + OrderItem ثم يجرب يضيف صف في Google Sheet (لا يفشل الطلب لو فشل الشيت).
    """
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # إنشاء الطلب
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=data.get('customer_name', '') or '',
            customer_phone=data.get('customer_phone', '') or '',
            customer_email=data.get('customer_email', '') or '',
            customer_city=data.get('customer_city', '') or '',
            customer_address=data.get('customer_address', '') or '',
            status='pending',
            total=Decimal('0.00')
        )

        total = Decimal('0.00')
        created_items = []

        items_data = data.get('items', [])
        for it in items_data:
            prod_id = it.get('product_id')
            qty = int(it.get('quantity', 0))
            if qty <= 0:
                continue
            try:
                product = Product.objects.get(id=prod_id)
            except Product.DoesNotExist:
                transaction.set_rollback(True)
                return Response({'detail': f'Product id {prod_id} not found'}, status=status.HTTP_400_BAD_REQUEST)

            # افترض أن لديك دالة على الموديل لإرجاع سعر الوحدة حسب الكمية
            unit_price = getattr(product, 'get_price_for_quantity', None)
            if callable(unit_price):
                unit_price = Decimal(unit_price(qty))
            else:
                unit_price = Decimal(product.base_price)

            oi = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=unit_price
            )
            created_items.append(oi)
            total += (unit_price * qty)

        # حدّث إجمالي الطلب
        order.total = total
        order.save(update_fields=['total'])

        # جهّز صف لإرساله للشيت
        try:
            items_desc = []
            for it in created_items:
                prod_name = getattr(it.product, 'name', str(it.product))
                items_desc.append(f"{prod_name} x{it.quantity} @ {it.unit_price}")
            items_str = " | ".join(items_desc)

            row = [
                str(order.id),
                order.customer_name or '',
                order.customer_phone or '',
                order.customer_email or '',
                order.customer_city or '',
                order.customer_address or '',
                items_str,
                str(order.total),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(order, 'created_at', None) else ''
            ]
            # نضع append داخل try/except لأننا لا نريد فشل إنشاء الطلب لو الشيت فشل
            try:
                append_order_to_sheet(row)
            except Exception as e:
                # سجل الخطأ لكن لا ترميه - الطلب تم إنشاؤه بنجاح
                logger.exception("Failed to append order to Google Sheet: %s", e)
        except Exception as ex:
            # لو حدث أي خطأ أثناء تجهيز الصف لا نلغي الطلب، فقط نسجل
            logger.exception("Error preparing row for Google Sheets: %s", ex)

        out = OrderReadSerializer(order, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)
