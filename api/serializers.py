import pyotp
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .groups import assign_role_and_save
from .models import *

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    print('serializer started')
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'role', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        print('validated')
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Password fields didnt match.'})
        return attrs

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        role = validated_data.pop('role')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(first_name=first_name, last_name=last_name, email=email, password=password)
        user.is_active = False

        # generate secret after registration
        user.otp_secret = pyotp.random_base32()
        print(f'otp secret created: {user.otp_secret}')
        user.set_password(password)

        # assign the role and save the user
        assign_role_and_save(user, role)
        return user

class UserListSerializer(serializers.ModelSerializer):
    role  = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = '__all__'
    def get_role(self, obj):
        # This method retrieves the group names as a comma-separated string
        return ', '.join(obj.groups.values_list('name', flat=True))

class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        # Get the standard token
        token = super().get_token(user)

        # Add custom claims
        role = user.groups.first()  # Get the user's first group (role)
        token['role'] = role.name if role else None  # Add role to the token
        token['email'] = user.email  # Add email to the token

        return token


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = '__all__'


class PurchaseRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseRequest
        fields = '__all__'

class RequestForQoutationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RequestForQoutation
        fields = '__all__'

class AbstractOfQoutationSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQoutation.objects.all(), write_only=True)
    rfq_details = RequestForQoutationSerializer(source='rfq', read_only=True)

    class Meta:
        model = AbstractOfQoutation
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True}
        }

class ItemQuotationSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), write_only=True)
    item_details = ItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = ItemQuotation
        fields = '__all__'  # Include all model fields
        extra_kwargs = {
            'item': {'write_only': True},     # Specify item as write-only
            'item_details': {'read_only': True}  # Specify item_details as read-only
        }


class ItemSelectedForQuoteSerializer(serializers.ModelSerializer):
    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQoutation.objects.all(), write_only=True)
    rfq_details = RequestForQoutationSerializer(source='rfq', read_only=True)

    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    item_q = serializers.PrimaryKeyRelatedField(queryset=ItemQuotation.objects.all(), write_only=True)
    item_details = ItemQuotationSerializer(source='item_q', read_only=True)

    class Meta:
        model = ItemSelectedForQuote
        fields = '__all__'

        extra_kwargs = {
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True},
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'item_q': {'write_only': True},
            'item_details': {'read_only': True},
        }

class RequesitionerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Requesitioner
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class InspectionAcceptanceReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectionAcceptanceReport
        fields = '__all__'


class RequisitionIssueSlipSerializer(serializers.ModelSerializer):

    class meta:
        model = RequisitionIssueSlip
        fields = '__all__'
