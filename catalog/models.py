from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "SubCategory"
        verbose_name_plural = "SubCategories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} — {self.name}"
        


class Product(models.Model):
    
    """
    موديل المنتج الأساسي.
    كل منتج له سعر افتراضي (base_price). التسعير حسب الكمية محفوظ في QuantityPrice.
    """
    sku = models.CharField(max_length=64,unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.sku} - {self.name}"

    def get_price_for_quantity(self, qty: int):
        
        """
        يعيد سعر الوحدة المناسب للكمية qty بناءً على شرائح الكمية المرتبطة بالمنتج.
        آلية العمل:
          - نحصل على كل الشرائح المرتبطة بهذا المنتج (quantity_prices).
          - نرتبها نزولياً حسب min_qty علشان نختار أعلى شريحة تنطبق.
          - إذا لم توجد شريحة مناسبة نرجع base_price.
        """
        tiers = self.quantity_prices.order_by('-min_qty')  # related_name في QuantityPrice
        for t in tiers:
            if qty >= t.min_qty and (t.max_qty is None or qty <= t.max_qty):
                return t.price
        return self.base_price

class QuantityPrice(models.Model):
    """
    شريحة سعر حسب الكمية:
      - min_qty: أقل كمية تنطبق (شاملة)
      - max_qty: أعلى كمية تنطبق (يمكن تركه None ليعني لا حد أعلي)
      - price: سعر الوحدة عند هذه الشريحة
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_prices')
    min_qty = models.PositiveIntegerField(help_text='Minimum quantity (inclusive)')
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text='Maximum quantity (optional)')
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['product', '-min_qty']
        verbose_name = 'Quantity price'
        verbose_name_plural = 'Quantity prices'

    def __str__(self):
        if self.max_qty:
            return f"{self.product.sku}: {self.min_qty}–{self.max_qty} => {self.price}"
        return f"{self.product.sku}:{self.min_qty}+=>{self.price}"






       