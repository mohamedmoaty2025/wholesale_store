# accounts/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile
from django.utils.html import format_html

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(admin.ModelAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_orders_count', 'get_total_spent', 'get_vip', 'is_staff')
    search_fields = ('username','email','profile__vip_status')
    list_filter = ('is_staff','profile__vip_status')

    def get_orders_count(self, obj):
        try:
            return obj.profile.orders_count
        except Exception:
            return 0
    get_orders_count.short_description = 'Orders'

    def get_total_spent(self, obj):
        try:
            return obj.profile.total_spent
        except Exception:
            return 0
    get_total_spent.short_description = 'Total Spent'

    def get_vip(self, obj):
        try:
            badge = obj.profile.vip_status
            color = 'green' if badge == 'vip' else ('orange' if badge == 'wholesale' else 'gray')
            return format_html(f'<b style="color:{color}">{badge}</b>')
        except Exception:
            return 'normal'
    get_vip.short_description = 'VIP'

# Unregister default User admin and register ours
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
try:
    admin.site.unregister(User)
except Exception:
    pass

admin.site.register(User, CustomUserAdmin)
