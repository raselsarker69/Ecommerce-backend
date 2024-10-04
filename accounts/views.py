from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from . import serializers
from . import models
from . import utils
from .utils import send_link_for_pass_set
#from .utils import utils  
from django.urls import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication

# Register view
class RegisterView(generics.CreateAPIView):
    serializer_class = serializers.RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)


# Login view
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.MyTokenObtainPairSerializer


# Logout view
class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]  
    permission_classes = [IsAuthenticated]  
    serializer_class = serializers.LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh_token']
                # Blacklist refresh token
                RefreshToken(refresh_token).blacklist()
                return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error blacklisting token: {e}") 
                return Response({'error': 'Invalid token or token already blacklisted.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# OTP Authentication
class VarifyOtpviewset(APIView):
    serializer_class = serializers.OtpTakerSerializer  

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            token1 = serializer.validated_data['token1']
            token2 = serializer.validated_data['token2']
            Email_varification_obj = models.Email_varification.objects.filter(
                email=email, otp=otp, token1=token1, token2=token2).first()

            if Email_varification_obj and Email_varification_obj.is_otp_valid:
                user = User.objects.get(email=email)
                user.is_active = True
                user.save()
                Refresh = RefreshToken.for_user(user)


                return Response({
                    'message': 'Registration successful.', 
                    'user_id':  user.id, 
                    "access": str(Refresh.access_token), 
                    "status": 1,
                    'refresh': str(Refresh)
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "OTP is invalid", "status": 0}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
        
        
        
# Password change view
class PasswordChangeView(APIView):
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'An error occurred while changing the password.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import logging
# logger instance
logger = logging.getLogger(__name__)


# Request password reset view
class RequestPasswordReset(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ResetPasswordRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()

        if user and not user.is_active:
            return Response({"error": "Inactive user. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)

        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            
            # Encode the user’s primary key as uidb64
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build the full URL dynamically using request.build_absolute_uri
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            reset_url = request.build_absolute_uri(relative_link)

            # Send email with the reset link
            link_sent = utils.send_link_for_pass_set(email, reset_url)
            if not link_sent:
                logger.error(f"Failed to send password reset email to {email}")
                return Response({"error": "Failed to send the reset link."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        else:
            # Return the same success response even if the email does not exist
            return Response({"message": "If the email is associated with an account, a password reset link has been sent."}, status=status.HTTP_200_OK)
        
        

# class RequestPasswordReset(APIView):
#     permission_classes = [AllowAny]
#     serializer_class = serializers.ResetPasswordRequestSerializer

#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         email = serializer.validated_data['email']
#         user = User.objects.filter(email__iexact=email).first()

#         if user and not user.is_active:
#             return Response({"error": "Inactive user. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)

#         if user:
#             token_generator = PasswordResetTokenGenerator()
#             token = token_generator.make_token(user)
            
#             # Encode the user’s primary key as uidb64
#             uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
#             # Generate the reset URL with the correct uidb64 and token
#             reset_url = f"http://127.0.0.1:8000/auth/reset-password/{uidb64}/{token}/"

#             # Send email with the reset link
#             link_sent = utils.send_link_for_pass_set(email, reset_url)
#             if not link_sent:
#                 return Response({"error": "Failed to send the reset link."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "No user found with this email."}, status=status.HTTP_404_NOT_FOUND)



# Reset password view
class ResetPassword(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']

        reset_obj = models.PasswordReset.objects.filter(token=token).first()

        if not reset_obj:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=reset_obj.email).first()

        if user:
            try:
                user.set_password(new_password)
                user.save()
                reset_obj.delete()  # Delete the reset token once used
                return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': 'Failed to reset the password.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'No user found with this email.'}, status=status.HTTP_404_NOT_FOUND)
