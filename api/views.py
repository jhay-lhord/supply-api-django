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
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth import logout
from datetime import timedelta
from django.utils.timezone import now
from django.db.models.functions import TruncDate
from django.db.models import Count


from .models import *
from .resend import send_mail_resend
from .serializers import *
from .serializers import CreateUserSerializer
from .tokens import get_tokens_for_user, token_decoder
from dotenv import load_dotenv
import os

load_dotenv()

is_production = os.getenv("DJANGO_ENV") == "production"


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
            return Response({"message": "User updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginTokenObtainPairView(TokenObtainPairView):
    """
    Login User credentials
    """
    serializer_class = LoginTokenObtainPairSerializer
    authentication_classes = [CookieJWTAuthentication]
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
        
class UserInformationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        return Response({
            'fullname': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'role' : user.groups.first().name if user.groups.first() else None,
        })


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
                        'email': user.email,
                        'role': role.name if role else None,
                        'fullname': f'{user.first_name} {user.last_name}'
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
                        secure=is_production,
                        samesite='None'
                    )
                    response.set_cookie(
                        key='access_token',
                        value=str(refresh.access_token),
                        httponly=True,
                        secure=is_production, 
                        samesite='None'
                    )

                    return response

                else:
                    return Response({'error': 'Invalid or Expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User Does not Exist'}, status=status.Http_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        print(f"Refresh Token: {refresh_token}")
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)

                response = Response({'message': 'Token refreshed',  'access_token': access_token})
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=is_production,
                    samesite='None',
                    max_age=3600,
                )
                return response
            except Exception:
                return Response({'error': 'Invalid refresh token'}, status=400)

        return Response({'error': 'No refresh token provided'}, status=400)



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
    


class LogoutAPIView(APIView):
    """
    API endpoint for logging out the user.
    """
    def post(self, request, *args, **kwargs):
        logout(request)

        response = Response({"message": "Logged out successfully."})

        # Clear both tokens
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')

        return response


class RecentActivityList(generics.ListAPIView):
    queryset = RecentActivity.objects.all()
    serializer_class = RecentActivitySerializer
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
         
        # Active Purchase Request
        active_pr = (
            PurchaseRequest.objects
            .annotate(day=TruncDate("created_at"))  # Annotate with day of week
            .values("day") 
            .annotate(total_active_pr=Count("pr_no"))  # Aggregate the count field
        )
        # Purchase Request in Progress
        inprogress_pr = (
            PurchaseRequest.objects.filter(status="Forwarded to Procurement")
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_inprogress_pr=Count("pr_no"))
        )
        # order in progress
        inprogress_po = (
            PurchaseOrder.objects.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_inprogress_po=Count("po_no"))
        )
        # Initialize Combined Data for the last 7 days
        date_range = [(now() - timedelta(days=i)).date() for i in range(7)]
        combined_data = {day.strftime("%b %d"): {"day": day.strftime("%b %d"), "total_active_pr": 0, "total_inprogress_pr": 0, "total_inprogress_po": 0} for day in date_range}
        # Process and Combine Data
        for data, key in zip([active_pr, inprogress_pr, inprogress_po], ["total_active_pr", "total_inprogress_pr", "total_inprogress_po"]):
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
