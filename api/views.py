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
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import *
from .resend import send_mail_resend
from .serializers import *
from .serializers import CreateUserSerializer
from .tokens import get_tokens_for_user, token_decoder


class RegisterUserAPIView(generics.CreateAPIView):
    """
    Register a new User
    """
    serializer_class = CreateUserSerializer
    authentication_classes = [JWTAuthentication]
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
                send_mail_resend(user.email, subject, message_html)

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


class LoginTokenObtainPairView(TokenObtainPairView):
    """
    Login User credentials
    """
    serializer_class = LoginTokenObtainPairSerializer
    authentication_classes = [JWTAuthentication]
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

            return Response({'message': 'OTP sent to your email, Please verify'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
                    print(user.last_login)

                    # Add custom claims to the token (email and role)
                    role = user.groups.first()
                    refresh['role'] = role.name if role else None
                    refresh['email'] = user.email

                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'message': 'Login Successfully'
                    },
                                    status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid or Expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User Does not Exist'}, status=status.Http_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserList(generics.ListCreateAPIView):
    """
    List all Users or Create new User
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a User
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    authentication_classes = [JWTAuthentication]
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

class PurchaseRequestItemList(generics.ListCreateAPIView):
    """
    List all Purchase Request Associated with Item
    """
    # queryset = PurchaseRequestItem.objects.select_related('purchase_request', 'item')
    queryset = PurchaseRequestItem.objects.all()
    serializer_class = PurchaseRequestItemSerializer
    authentication_classes = []
    permission_classes = []


class ItemList(generics.ListCreateAPIView):
    """
    List all Item, or create a new item
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = []
    permission_classes = []


class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Item instance
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseRequestList(generics.ListCreateAPIView):
    """
    List all Purchase request, or create a new Purchase request
    """
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    authentication_classes = []
    permission_classes = []


class PurchaseRequestDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase request instance
    """
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierList(generics.ListCreateAPIView):
    """
    List all Supplier, or create a new Supplier
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Supplier instance
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseOrderList(generics.ListCreateAPIView):
    """
    List all Purchase Order, or create a new Purchase Order
    """
    queryset = PurchaseOrder.objects.select_related('item').all()
    serializer_class = PurchaseOrderSerializer
    authentication_classes = []
    permission_classes = []


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase Order instance
    """
    queryset = PurchaseOrder.objects.select_related('item').all()
    serializer_class = PurchaseOrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class InspectionAcceptanceReportList(generics.ListCreateAPIView):
    """
    List all  Inspection report , or create a new Inspection report
    """
    queryset = InspectionAcceptanceReport.objects.select_related('supplier', 'item', 'purchaseOrder').all()
    serializer_class = InspectionAcceptanceReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class InspectionAcceptanceReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Inspection report instance
    """
    queryset = InspectionAcceptanceReport.objects.select_related('supplier', 'item', 'purchaseOrder').all()
    serializer_class = InspectionAcceptanceReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequisitionIssueSlipList(generics.ListCreateAPIView):
    """
    List all  Requisition Slip , or create a new  Requisition Slip
    """
    queryset = RequisitionIssueSlip.objects.select_related('item').all()
    serializer_class = RequisitionIssueSlipSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class RequisitionIssueSlipDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Requisition Slip instance
    """
    queryset = RequisitionIssueSlip.objects.all()
    serializer_class = RequisitionIssueSlipSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
