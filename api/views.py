from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView
from .auth import CookieJWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth import logout
from datetime import timedelta
from django.utils.timezone import now
from django.db.models.functions import TruncDate
from django.db.models import Count

from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import *
from .models import *
from .resend import send_mail_resend, send_file
from .serializers import *
from .serializers import *
from .tokens import get_tokens_for_user, token_decoder
from dotenv import load_dotenv
import os

load_dotenv()

is_production = os.getenv('IS_PRODUCTION', 'False').lower() == 'true'


class RegisterUserAPIView(generics.CreateAPIView):
    """
    Register a new User
    """
    serializer_class = CreateUserSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)

        if serializer.is_valid():

            try:
                user = serializer.save()
                user.save()
                token = get_tokens_for_user(user)

                # Get the current domain
                current_site = get_current_site(request)
                activation_link = f'http://{current_site.domain}/api/user/activate/{token["access"]}'

                message_html =  f'''<h2 style="color: #333333;">Account Created Successfully - Pending Activation</h2>
                                <p>Dear <strong>{user.first_name}</strong>,</p>
                                <p> Your account has been successfully created! To complete the setup, an administrator needs to activate your account. 
                                You will receive a email notification once the activation is complete.</p>
            
                                <p>If you have any questions or need assistance, feel free to reach out to our support team at <a href="mailto:manilajaylord_24@gmail.com">our support Email</a>.</p>
                                <p>We look forward to serving you!</p>

                                 <p>
                                    <em style="color: #999999;">This is a system-generated email. Please do not reply directly to this message.</em>
                                </p>

                                <p>Best regards,</p>
                                <p>Supply Office<br>
                                Team SlapSoil<br>
                                </p>'''
                subject = "Account Created Successfully - Pending Activation"

                # Send activation email
                if(is_production):
                    send_mail_resend(user.email, subject, message_html)
                else:
                    print(f"[{user.email}] Account Created Successfully - Pending Activation")

            except IntegrityError as e:
                if 'duplicate key value violates unique constraint' in str(e):
                    return Response({'email': 'A user with this email already exists.'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': 'An error occured while creating the user'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateUserAPIView(APIView):
    """
    Activate a new registered user
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        # Decode the token to get the user id
        user_id = token_decoder(token)

        # Attempt to retrieve the user and activate the account
        try:
            user = get_object_or_404(User, pk=user_id)
            user.is_active = True
            user.save()
            return render(request, 'activation_success.html', status=status.HTTP_200_OK)
        except Http404:
            return render(request, 'activation_failed.html', status=status.HTTP_400_BAD_REQUEST)
        
class EditUserView(APIView):
    """
    Edit User Profile
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomUserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.groups.first().name if user.groups.exists() else "User",
            }
            return Response({
                        'message': 'Updated Successfully',
                        'user': user_data,
                    }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginTokenObtainPairView(TokenObtainPairView):
    """
    Login User credentials
    """
    serializer_class = LoginTokenObtainPairSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            # generate OTP
            user.generate_otp()

            subject = 'Your OTP Code'
            message_html = f'<p>Your OTP code is <strong>{user.otp_code}</strong>. It is valid for 5 minutes.</p>'

            # send_OTP_mail(user.email, subject, message_html )
            send_mail_resend(user.email, subject, message_html)

            return Response({'message': f"We've sent a verification code to {user.email}. Please check your inbox and verify your account.", 'email': user.email}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            return Response({
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.groups.first().name if user.groups.exists() else "User",
            })
        except Exception as e:
            raise AuthenticationFailed("Invalid token or user not authenticated")


class OTPVerificationView(APIView):
    """
    OTP Verification View
    """
    permission_classes = []
    authentication_classes = []
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']

            try:
                user = CustomUser.objects.get(email=email)

                if user.verify_otp(otp_code):
                    refresh = RefreshToken.for_user(user)
                    user.last_login = timezone.now()
                    user.save()

                    # Add custom claims to the token (email and role)
                    role = user.groups.first()
                    refresh['role'] = role.name if role else None
                    refresh['email'] = user.email
                    refresh['fullname'] = f'{user.first_name} {user.last_name}'
                    
                    user = {
                        'id': user.id,
                        'email': user.email,
                        'role': role.name if role else None,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                    
                    # Create the response object
                    response = Response({
                        'message': 'Login Successfully',
                        'user': user,
                    }, status=status.HTTP_200_OK)
                    
                    # Set tokens as HTTP-only cookies
                    response.set_cookie(
                        key='refresh_token',
                        value=str(refresh),
                        httponly=True,
                        secure=True,
                        samesite='None' if not is_production else 'Lax'
                    )
                    response.set_cookie(
                        key='access_token',
                        value=str(refresh.access_token),
                        httponly=True,
                        secure=True, 
                        samesite='None' if not is_production else 'Lax'
                    )

                    return response

                else:
                    return Response({'error': 'Invalid or Expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User Does not Exist'}, status=status.Http_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ResendOTPView(APIView):
    """
    Resend OTP View
    """
    permission_classes = []
    authentication_classes = []
    serializer_class = ResendOTPSerializer

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = CustomUser.objects.get(email=email)

                # generate new OTP
                user.generate_otp()

                subject = 'Your OTP Code'
                message_html = f'<p>Your new OTP code is <strong>{user.otp_code}</strong>. It is valid for 5 minutes.</p>'

                # send_OTP_mail(user.email, subject, message_html )
                send_mail_resend(user.email, subject, message_html)

                return Response({
                    'message': 'OTP has been resent to your email address.'
                }, status=status.HTTP_200_OK)

            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'User does not exist with this email address.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'No refresh token provided'}, status=400)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            response = Response({'message': 'Token refreshed', 'access_token': access_token})
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=is_production,  # Ensure `is_production` is defined correctly
                samesite='None',
                max_age=3600,  # Token lifespan in seconds
            )
            return response

        except InvalidToken:
            return Response({'error': 'Invalid or expired refresh token'}, status=401)

        except Exception as e:
            return Response({'error': f'Unexpected error: {str(e)}'}, status=500)


class LoginTokenOfflineView(TokenObtainPairView):
    """
    Offine Login Verification View using email and password
    """

    serializer_class = LoginTokenObtainPairSerializer
    authentication_classes = [] 
    
    def post(self, request, *args, **kwargs):   
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate user with email and password
        user = authenticate(request, email=email, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save()

            # Add custom claims to the token (email and role)
            role = user.groups.first()
            refresh['role'] = role.name if role else None
            refresh['email'] = user.email
            refresh['fullname'] = f'{user.first_name} {user.last_name}'

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login Successful'
            }, status=status.HTTP_200_OK)
        
        # If authentication fails, return an error
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
    


class LogoutView(APIView):
    """
    Logout view
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            # Retrieve the refresh token from cookies or request data
            refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')

            if not refresh_token:
                return Response({"detail": "Refresh token is required"}, status=400)

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            print("Token Blacklisted and cant be used in future authentication")

            # Optionally delete tokens from cookies
            response = Response({"message": "Logout successful"})
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        except TokenError as e:
            return Response({"detail": "Invalid token"}, status=400)
        except Exception as e:
            return Response({"detail": f"Error during logout: {str(e)}"}, status=500)
        
class ChangePasswordView(APIView):
    """
    Change Password View
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class RecentActivityList(generics.ListAPIView):
    """
    List recent activities created within the last 7 days.
    """
    serializer_class = RecentActivitySerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        seven_days_ago = now() - timedelta(days=7)
        queryset = RecentActivity.objects.filter(timestamp__gte=seven_days_ago).select_related('user', 'content_type')
        return queryset 
    
    

class SendFileView(APIView):
    """
    Send File View
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]  
    
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        file = request.FILES.get("file")
        
        message_html = f"""
        <div>
        <div>
            <h1>Request for Quotation</h1>
        </div>
        <div>
            <p>Dear <strong>Valued Supplier</strong>,</p>
            <p>We are currently canvassing items and would like to request a quotation for the attached file. Please review the details of the requested items and provide your best price, terms, and conditions at your earliest convenience.</p>
            <p>If you have any questions or require further clarification, please feel free to contact us at this email address.</p>
            <p>Thank you for your prompt attention to this matter. We look forward to your response.</p>
        </div>
        <p>
            <em style="color: #999999;">This is a system-generated email. Please do not reply directly to this message.</em>
        </p>
        <p>Best regards,</p>
            <p>Supply Office<br>
            Team SlapSoil<br>
        </div>
        """

        response = send_file(file, email, message_html)

        if "error" in response:
            return Response(
                {"message": f"Failed to send email: {response['error']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": f"Email sent successfully to {email} with the attached file!"},
            status=status.HTTP_200_OK,
        )
        
        
class TrackStatusListView(ListAPIView):
    """
    Views for filtering status in Purchase Request
    """

    queryset = TrackStatus.objects.all().order_by('-updated_at')
    serializer_class = TrackStatusSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrackStatusFilter
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]



class UserList(generics.ListCreateAPIView):
    """
    List all Users or Create new User
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequisitionerList(generics.ListCreateAPIView):
    """
    List all Requisitioner or Create new Requisitioner
    """
    queryset = Requesitioner.objects.all()
    serializer_class = RequesitionerSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequisitionerDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Requisitioner
    """
    queryset = Requesitioner.objects.all()
    serializer_class = RequesitionerSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class CampusDirectorList(generics.ListCreateAPIView):
    """
    List all CampusDirector or Create new CampusDirector
    """
    queryset = CampusDirector.objects.all()
    serializer_class = CampusDirectorSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class CampusDirectorDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a CampusDirector
    """
    queryset = CampusDirector.objects.all()
    serializer_class = CampusDirectorSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class BACMemberList(generics.ListCreateAPIView):
    """
    List all BACMember or Create new BACMember
    """
    queryset = BACMember.objects.all()
    serializer_class = BACMemberSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class BACMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a BACMember
    """
    queryset = BACMember.objects.all()
    serializer_class = BACMemberSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a User
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        # Check if a specific field 'is_active' has changed
        is_active_before = user.is_active

        response = super().partial_update(request, *args, **kwargs)

        user.refresh_from_db()  # Refresh user to get the updated state
        message_html =  f'''<h2 style="color: #333333;">Account Activation Successfull</h2>
            <p>Dear <strong>{user.first_name}</strong>,</p>
            <p>We are pleased to inform you that your account has been successfully activated. You can now access all the features and services available to you.</p>
            <p>To get started, please log in to your account</p>
            
            <p>If you have any questions or need assistance, feel free to reach out to our support team at <a href="mailto:manilajaylord_24@gmail.com">our support Email</a>.</p>
            <p>We look forward to serving you!</p>
            <p>
                <em style="color: #999999;">This is a system-generated email. Please do not reply directly to this message.</em>
            </p>
            <p>Best regards,</p>
            <p>Supply Office<br>
            Team SlapSoil<br>
            </p>'''
        if not is_active_before and user.is_active:
            send_mail_resend(user.email, "Account Activation Successfull", message_html)

        return response


class ItemList(generics.ListCreateAPIView):
    """
    List all Item, or create a new item
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Item instance
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ItemsDetail(APIView):
    """
    Retrieve Items in Purchase Request instance
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, field_name, value, *args, **kwargs):
        # only the purchase_request is allowed to filter
        allowed_fields = ['purchase_request']  # example fields

        if field_name not in allowed_fields:
            return Response({
                'error': 'Field not allowed for filtering'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        filter_kwargs = {field_name: value}
        items = Item.objects.filter(**filter_kwargs)

        if not items.exists():
            return Response({
                'error': 'Error getting Items in Purchase Request'
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize the items before sending back to front-end
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PurchaseRequestList(generics.ListCreateAPIView):
    """
    List all Purchase request, or create a new Purchase request
    """
    queryset = PurchaseRequest.objects.select_related("requisitioner", "campus_director")
    serializer_class = PurchaseRequestSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseRequestDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase request instance
    """
    queryset = PurchaseRequest.objects.select_related("requisitioner", "campus_director")
    serializer_class = PurchaseRequestSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

class PurchaseRequestUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            purchase_request = PurchaseRequest.objects.get(pk=pk)
            serializer = PurchaseRequestSerializer(purchase_request, data=request.data, partial=True)
            if serializer.is_valid():
                purchase_request.updated_at = timezone.now()
                purchase_request.save()
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PurchaseRequest.DoesNotExist:
            return Response({"error": "Purchase Request not found"}, status=status.HTTP_404_NOT_FOUND)


class PurchaseRequestMOPUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            purchase_request = PurchaseRequest.objects.get(pk=pk)
            serializer = PurchaseRequestSerializer(purchase_request, data=request.data, partial=True)
            if serializer.is_valid():
                purchase_request.updated_at = timezone.now()
                purchase_request.save()
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PurchaseRequest.DoesNotExist:
            return Response({"error": "Purchase Request not found"}, status=status.HTTP_404_NOT_FOUND)



class PurchaseRequestStatusUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            purchase_request = PurchaseRequest.objects.get(pk=pk)
            serializer = PurchaseRequestSerializer(purchase_request, data=request.data, partial=True)
            if serializer.is_valid():
                purchase_request.updated_at = timezone.now()
                purchase_request.save()
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PurchaseRequest.DoesNotExist:
            return Response({"error": "Purchase Order not found"}, status=status.HTTP_404_NOT_FOUND)
        

class ItemsFilterListView(ListAPIView):
    """
    Views for filtering item in Purchase Request
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ItemsFilter
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequestForQoutationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Request For Qoutation instance
    """
    queryset = RequestForQoutation.objects.all()
    serializer_class = RequestForQoutationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequestForQoutationList(generics.ListCreateAPIView):
    """
    List all Request for Qoutation, or create a new Request For Qoutation
    """
    queryset = RequestForQoutation.objects.all()
    serializer_class = RequestForQoutationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ItemQuotationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Item Qoutation instance
    """
    queryset = ItemQuotation.objects.all()
    serializer_class = ItemQuotationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ItemQuotationList(generics.ListCreateAPIView):
    """
    List all Item Quotaion or create a new Item Qoutation
    """
    queryset = ItemQuotation.objects.all()
    serializer_class = ItemQuotationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class AbstractOfQoutationList(generics.ListCreateAPIView):
    """
    List all Abstract for Quotation or create new Abstract for Quotation
    """
    queryset = AbstractOfQuotation.objects.all()
    serializer_class = AbstractOfQoutationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class AbstractOfQoutationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete Abstract of Quotation instance
    """
    queryset = AbstractOfQuotation.objects.all()
    serializer_class = AbstractOfQoutationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierList(generics.ListCreateAPIView):
    """
    List all Supplier, or create a new Supplier
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Supplier instance
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
class SupplierUpdateIsAddedToTrueView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
            serializer = SupplierSerializer(supplier, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)



class SupplierItemList(generics.ListCreateAPIView):
    """
    List all Item, or create a new Item
    """
    queryset = SupplierItem.objects.all()
    serializer_class = SupplierItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Item instance
    """
    queryset = SupplierItem.objects.all()
    serializer_class = SupplierItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class BACMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a BACMember instance
    """
    queryset = BACMember.objects.all()
    serializer_class = BACMemberSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class BACMemberList(generics.ListCreateAPIView):
    """
    List all BACMember or create a new BACMember
    """
    queryset = BACMember.objects.all()
    serializer_class = BACMemberSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseOrderList(generics.ListCreateAPIView):
    """
    List all Purchase Order, or create a new Purchase Order
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase Order instance
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

class PurchaseOrderStatusUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            serializer = PurchaseOrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                order.updated_at = timezone.now()
                order.save()
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PurchaseOrder.DoesNotExist:
            return Response({"error": "Purchase Order not found"}, status=status.HTTP_404_NOT_FOUND)

class PurchaseOrderItemList(generics.ListCreateAPIView):
    """
    List all Purchase Order Item, or create a new Purchase Order Item
    """
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseOrderItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase Order Item instance
    """
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class BACDailyReportView(APIView):
    """
    BAC Daily Reports View for the past 7 days.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, *args, **kwargs):   
        seven_days_ago = now() - timedelta(days=7)
        
        # Approved Data
        approved = (
            PurchaseRequest.objects.filter(status="Forwarded to Procurement", created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_approved=Count("pr_no"))
        )
        # Quotation Data
        quotation = (
            RequestForQoutation.objects.filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_quotation=Count("rfq_no"))
        )
        # Abstract Data
        abstract = (
            AbstractOfQuotation.objects.filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_abstract=Count("aoq_no"))
        )
        # Initialize Combined Data for the Last 7 Days
        date_range = [(now() - timedelta(days=i)).date() for i in range(7)]
        combined_data = {day.strftime("%b %d"): {"day": day.strftime("%b %d"), "total_approved": 0, "total_quotation": 0, "total_abstract": 0} for day in date_range}

        # Combine Data
        for data, key in zip([approved, quotation, abstract], ["total_approved", "total_quotation", "total_abstract"]):
            for entry in data:
                day_str = entry["day"].strftime("%b %d")
                if day_str in combined_data:
                    combined_data[day_str][key] = entry[key]

        # Convert Combined Data to List
        response_data = list(combined_data.values())
        return Response(response_data, status=status.HTTP_200_OK)


class SupplyDailyReportView(APIView):
    """
    Supply Daily Reports View for the past 7 days.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, *args, **kwargs):  
        seven_days_ago = now() - timedelta(days=7)
         
        # All Purchase Request
        purchase_request = (
            PurchaseRequest.objects
            .annotate(day=TruncDate("created_at"))  # Annotate with day of week
            .values("day") 
            .annotate(total_purchase_request=Count("pr_no"))  # Aggregate the count field
        )
        # All Purchase Order
        purchase_order = (
            PurchaseOrder.objects
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_purchase_order=Count("po_no"))
        )
        # Initialize Combined Data for the last 7 days
        date_range = [(now() - timedelta(days=i)).date() for i in range(7)]
        combined_data = {day.strftime("%b %d"): {"day": day.strftime("%b %d"), "total_purchase_request": 0, "total_purchase_order": 0} for day in date_range}
        # Process and Combine Data
        for data, key in zip([purchase_request, purchase_order], ["total_purchase_request", "total_purchase_order"]):
            for entry in data:
                day_str = entry["day"].strftime("%b %d")
                if day_str in combined_data:
                    combined_data[day_str][key] = entry[key]
        # Convert Combined Data to List
        response_data = list(combined_data.values())
        return Response(response_data, status=status.HTTP_200_OK)


class InspectionAndAcceptanceList(generics.ListCreateAPIView):
    """
    List all  Inspection and acceptance , or create a new Inspection and Acceptance
    """
    queryset = InspectionAndAcceptance.objects.all()
    serializer_class = InspectionAndAcceptanceSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class InspectionAndAcceptanceDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Inspection and Acceptance instance
    """
    queryset = InspectionAndAcceptance.objects.all()
    serializer_class = InspectionAndAcceptanceSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class DeliveredItemsList(generics.ListCreateAPIView):
    """
    List all  Delivered Items , or create a new Delivered Items
    """
    queryset = DeliveredItems.objects.all()
    serializer_class = DeliveredItemsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class DeliveredItemsDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a  Delivered Items instance
    """
    queryset = DeliveredItems.objects.all()
    serializer_class = DeliveredItemsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    
class DeliveredItemsFilterListView(ListAPIView):
    """
    Views for filtering Items delivered by Purchase Request
    """

    queryset = DeliveredItems.objects.all()
    serializer_class = DeliveredItemsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeliveredItemsFilter
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]



class StockItemsList(generics.ListCreateAPIView):
    """
    List all  Stocks Items , or create a new Stock Items
    """
    queryset = StockItems.objects.all()
    serializer_class = StockItemsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class StockItemsDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a  Stocks Items instance
    """
    queryset = StockItems.objects.all()
    serializer_class = StockItemsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class DeliveredItemsUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            delivered_items = DeliveredItems.objects.get(pk=pk)
            serializer = DeliveredItemsSerializer(delivered_items, data=request.data, partial=True)
            if serializer.is_valid():
                delivered_items.save()
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DeliveredItems.DoesNotExist:
            return Response({"error": "Delivered Item not found"}, status=status.HTTP_404_NOT_FOUND)



class RequisitionIssueSlipList(generics.ListCreateAPIView):
    """
    List all  Requisition Slip , or create a new  Requisition Slip
    """
    queryset = RequisitionIssueSlip.objects.select_related('item').all()
    serializer_class = RequisitionIssueSlipSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequisitionIssueSlipDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Requisition Slip instance
    """
    queryset = RequisitionIssueSlip.objects.all()
    serializer_class = RequisitionIssueSlipSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
