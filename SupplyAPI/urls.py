from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import ActivateUserAPIView, LoginTokenObtainPairView, OTPVerificationView, RegisterUserAPIView, LoginTokenOfflineView, CheckAuthView, RefreshTokenView, LogoutView, ResendOTPView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/check_auth', CheckAuthView.as_view(), name='user_info'),
    path('api/user/register/', RegisterUserAPIView.as_view(), name='register'),
    path('api/user/logout/', LogoutView.as_view(), name='logout'),
    path('api/user/activate/<str:token>/', ActivateUserAPIView.as_view(), name='activate'),
    path('api/user/login_token/', LoginTokenObtainPairView.as_view(), name='get_token'),
    path('api/user/login_token_offline/', LoginTokenOfflineView.as_view(), name='get_token_offline'),
    path('api/user/login_verify_otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('api/user/login_resend_otp/', ResendOTPView.as_view(), name='verify_otp'),
    path('api/token/refresh/', RefreshTokenView.as_view(), name='token'),
    path('api/', include('api.urls')),
]
