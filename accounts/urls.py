from django.urls import path
from .views import MyTokenObtainPairView, RegisterView, LogoutView, PasswordChangeView,RequestPasswordReset, ResetPassword
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('requestpasswordreset/', RequestPasswordReset.as_view(), name='RequestPasswordReset'),
    path('reset-password/<str:token>/', ResetPassword.as_view(), name='password-reset'),
]
