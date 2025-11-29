# catalog/urls.py

from rest_framework import routers
from .views import ProductViewSet
from . import views
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('categories/',views.CategoryListViews.as_view(),name ='category-list'),
    path('subcategories/', views.SubCategoryListViews.as_view(), name='subcategory-list'),
    path('categories/<int:category_id>/subcategoies/',views.SubCategoryListViews.as_view(),name = 'subcategory-create-list'),
    path('products/',views.ProductListViews.as_view(), name = 'product-list'),
    path('products/<int:id>/',views.ProductDetailView.as_view(),name='product-detail')
]
