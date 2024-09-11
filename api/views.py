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
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import *
from .resend import send_mail
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

                message_html = f'<p>Please activate your account by clicking the button below</p> <br><button><a href={activation_link}/>Activate</></button>'  # noqa: E501 ignore the line too long rule in flake8
                # Send activation email
                send_mail(
                    request.data['email'],
                    'Activate your Account',
                    message_html,
                )
                print(f'returned data after registeing {serializer.data}')
            except IntegrityError as e:
                if 'duplicate key value violates unique constraint' in str(e):
                    return Response({'detail': 'A user with this email already exists.'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'detail': 'An error occured while creating the user'},
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


class ItemList(generics.ListCreateAPIView):
    """
    List all Item, or create a new item
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


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
    queryset = PurchaseRequest.objects.select_related('user').all()
    serializer_class = PurchaseRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class PurchaseRequestDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase request instance
    """
    queryset = PurchaseRequest.objects.select_related('user').all()
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


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
