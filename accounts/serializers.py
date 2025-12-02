# accounts/serializers.py
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from rest_framework import serializers
from .models import Profile

User = get_user_model()


# ========== تسجيل مستخدم جديد ==========
class RegisterSerializer(serializers.ModelSerializer):
    # الحقول الإضافية (ليست في User model مباشرة)
    number_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'number_phone',
            'city',
            'address',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
        }

    def create(self, validated_data):
        # استخرج الحقول المتعلقة بالـ profile
        number = validated_data.pop('number_phone', '') or ''
        city = validated_data.pop('city', '') or ''
        address = validated_data.pop('address', '') or ''

        # استخرج كلمة السر
        password = validated_data.pop('password')

        try:
            with transaction.atomic():
                # أنشئ المستخدم عبر الواجهة الصحيحة للموديل
                user = User.objects.create_user(
                    username=validated_data.get('username'),
                    email=validated_data.get('email'),
                    password=password,
                    first_name=validated_data.get('first_name', '') or '',
                    last_name=validated_data.get('last_name', '') or ''
                )

                # احصل على البروفايل إن وُجد أو أنشئه (signal قد يكون أنشأه بالفعل)
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'number_phone': number,
                        'city': city,
                        'address': address,
                    }
                )

                # لو البروفايل سبق وُجد، حدّث الحقول القادمة من عملية التسجيل إن وُجدت
                if not created:
                    updated = False
                    if number:
                        profile.number_phone = number
                        updated = True
                    if city:
                        profile.city = city
                        updated = True
                    if address:
                        profile.address = address
                        updated = True
                    if updated:
                        profile.save()

                return user

        except IntegrityError:
            # حالة نادرة — انقضاض/تسابق: دع الـ view/handler يتعامل مع الخطأ أو رُميه
            raise


# ========== Profile Serializer ==========
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'orders_count',
            'total_spent',
            'last_order_date',
            'vip_status',
            'note',
            'number_phone',
            'city',
            'address',
        )


# ========== User Serializer ==========
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile',
        )
