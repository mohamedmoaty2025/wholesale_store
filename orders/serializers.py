from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from catalog.models import Product
from .models import Order, OrderItem

class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'unit_price')

class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class CreateOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_city = serializers.CharField(required=False, allow_blank=True)
    customer_address = serializers.CharField(required=False, allow_blank=True)

    items = CreateOrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("items must not be empty.")
        product_ids = [it['product_id'] for it in value]
        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(set(product_ids)):
            raise serializers.ValidationError("One or more products do not exist.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # إذا كان المستخدم مسجلاً في الـ request، استخدم بياناته
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None

        # استخدام بيانات المستخدم إذا كان مسجلاً
        customer_name = validated_data.get('customer_name', user.first_name + ' ' + user.last_name if user else '')
        customer_phone = validated_data.get('customer_phone', user.profile.mobile if user and user.profile else '')
        customer_email = validated_data.get('customer_email', user.email if user else '')
        customer_city = validated_data.get('customer_city', '')
        customer_address = validated_data.get('customer_address', user.profile.address if user and user.profile else '')

        # إنشاء الطلب مع استخدام بيانات العميل من request.user إذا كانت موجودة
        order = Order.objects.create(
            user=user,  # ربط الطلب بالمستخدم المسجل
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            customer_city=customer_city,
            customer_address=customer_address,
            total=Decimal('0.00'),
        )

        total = Decimal('0.00')

        product_map = {p.id: p for p in Product.objects.filter(id__in=[it['product_id'] for it in items_data])}

        for it in items_data:
            pid = it['product_id']
            qty = int(it['quantity'])
            product = product_map.get(pid)
            if not product:
                raise serializers.ValidationError(f"Product {pid} not found (race condition).")

            unit_price = product.base_price if getattr(product, 'base_price', None) is not None else Decimal('0.00')

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=unit_price
            )
            total += (unit_price * qty)

        order.total = total
        order.save(update_fields=['total'])

        return order

class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ('id', 'created_at', 'status', 'total',
                  'customer_name', 'customer_phone', 'customer_email', 'customer_city', 'customer_address',
                  'items')
