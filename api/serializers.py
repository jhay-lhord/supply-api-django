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


class PurchaseRequestItemSerializer(serializers.ModelSerializer):
    item_no = serializers.SerializerMethodField()
    pr_no = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseRequestItem
        fields = '__all__'

    def get_item_no(self, obj):
        item = obj.item
        return {
            'item_no': item.item_no,
            'item_description': item.item_description,
            'quantity': item.quantity,
            'unit_cost': item.unit_cost,
            'total_cost': item.total_cost,
        }

    def get_pr_no(self, obj):

        pr = obj.purchase_request
        return {
            'pr_no': pr.pr_no,
            'purpose': pr.purpose,
            'requested_by': pr.requested_by,
            'approved_by': pr.approved_by,
            'status': pr.status,
        }


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
