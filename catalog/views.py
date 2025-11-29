from django.shortcuts import render
# catalog/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status,serializers
from rest_framework import generics
from .models import Product , SubCategory,Category
from .serializers import ProductListSerializer, ProductDetailSerializer,SubCategorySerializer,CategorySerializer
from rest_framework.permissions import AllowAny


class CategoryListViews(generics.ListCreateAPIView):
    queryset = Category.objects.filter(active =True).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

# قائمة الفئات الداخلية لِـ category معين
class SubCategoryListViews(generics.ListCreateAPIView):
    serializer_class = SubCategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        cat_id = self.kwargs.get('category_id')
        qs = SubCategory.objects.filter(active = True)
        if cat_id:
            qs = qs.filter(category_id=cat_id)
        return qs.order_by('name')
    
    def perform_create(self, serializer):
        """
        عند انشاء فئة فرعية من خلال POST الى
        /api/categories/<category_id>/subcategories/
        نربطها بالـ Category المعطى في الـ URL.
        """
        cat_id = self.kwargs.get('category_id')
        if not cat_id:
            # إذا لم يُرسل category_id فسنرمي خطأ مناسب
            raise serializers.ValidationError({"category": "category_id (in URL) is required."})
        try:
            cat = Category.objects.get(id=cat_id)
        except Category.DoesNotExist:
            raise serializers.ValidationError({"category": "Category not found."})
        serializer.save(category=cat)

# قائمة المنتجات (قابلة للتصفية عبر query params)
class ProductListViews(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]  # التأكد من السماح للجميع برؤية المنتجات
    def get_queryset(self):
       qs = Product.objects.filter(active=True)
       # فلترة حسب category أو subcategory
       cat = self.request.query_params.get('category')
       sub = self.request.query_params.get('subcategory')
       if sub:
           qs =qs.filter(subcategory_id=sub)
       elif cat:
           qs =qs.filter(subcategory__category_id=cat)   
       return qs.order_by('name')
# تفاصيل منتج واحد
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(active=True)
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = 'id'
    
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet للقراءة فقط (list, retrieve) لمنتجات الكتالوج.
    يعمل action فرعي price-for-qty لحساب السعر بناءً على الكمية.
    """
    queryset = Product.objects.filter(active=True)
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=True, methods=['get'], url_path='price-for-qty')
    def price_for_qty(self, request, id=None):
        product = self.get_object()
        qty_param = request.query_params.get('qty', '1')
        try:
            qty = int(qty_param)
            if qty < 1:
                raise ValueError
        except Exception:
            return Response({'detail': 'Invalid qty parameter'}, status=status.HTTP_400_BAD_REQUEST)

        unit_price = product.get_price_for_quantity(qty)
        total = unit_price * qty
        return Response({
            'product_id': product.id,
            'qty': qty,
            'unit_price': str(unit_price),
            'total_price': str(total),
        })
