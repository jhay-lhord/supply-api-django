from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import ActivateUserAPIView, LoginTokenObtainPairView, RegisterUserAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/register/', RegisterUserAPIView.as_view(), name='register'),
    path('api/user/activate/<str:token>/', ActivateUserAPIView.as_view(), name='activate'),
    path('api/token/', LoginTokenObtainPairView.as_view(), name='get_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token'),
    path('api/', include('api.urls')),
]
