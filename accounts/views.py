# accounts/views.py
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta

from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    تسجيل مستخدم جديد ثم إصدار توكنات JWT:
    - access: في body
    - refresh: في HttpOnly cookie
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # اصدار توكنات JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # ضع refresh في كوكي HttpOnly
        response = Response({
            "user": UserSerializer(user).data,
            "access": access_token
        }, status=status.HTTP_201_CREATED)

        # تخصيص خصائص الكوكي — تأكد تغيير secure=True في الإنتاج مع HTTPS
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60
        )
        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    يستخدم المسلسل الافتراضي لينتج access & refresh، ثم ينقل refresh إلى HttpOnly cookie
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and 'refresh' in response.data:
            refresh = response.data.pop('refresh')
            access = response.data.get('access')

            response.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=False,  # غيّر لـ True في الإنتاج
                samesite='Lax',
                max_age=7 * 24 * 60 * 60
            )
            response.data['access'] = access
        return response


class CookieTokenRefreshView(APIView):
    """
    يقوم بقراءة refresh من الكوكي ويستخدم TokenRefreshSerializer للحصول على access جديد.
    لا نعدل request.data._mutable هنا.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh_token')
        if not refresh:
            return Response({'detail': 'No refresh cookie'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={'refresh': refresh})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

        response_data = serializer.validated_data  # سيحتوي على access وربما refresh جديد
        resp = Response(response_data, status=status.HTTP_200_OK)

        # إذا عاد refresh جديد (عند ROTATE_REFRESH_TOKENS=True) خزّنه في الكوكي
        if 'refresh' in response_data:
            new_refresh = response_data.pop('refresh')
            resp.set_cookie(
                key='refresh_token',
                value=new_refresh,
                httponly=True,
                secure=False,  # غيّر لـ True في الإنتاج
                samesite='Lax',
                max_age=7 * 24 * 60 * 60
            )
        return resp


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
