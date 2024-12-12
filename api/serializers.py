import pyotp
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .groups import assign_role_and_save
from .models import *

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('employee_id', 'first_name', 'last_name', 'role', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        print('validated')
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Password fields didnt match.'})
        return attrs

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        role = validated_data.pop('role')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email, password=password)
        user.is_active = False

        # generate secret after registration
        user.otp_secret = pyotp.random_base32()
        print(f'otp secret created: {user.otp_secret}')
        user.set_password(password)

        # assign the role and save the user
        assign_role_and_save(user, role)
        return user

class CustomUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

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

    
class RecentActivitySerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = RecentActivity
        fields = ['id', 'user', 'user_role', 'activity_type', 'timestamp', 'content_type', 'object_id']


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = '__all__'

class CampusDirectorSerializer(serializers.ModelSerializer):
    
    class Meta: 
        model = CampusDirector
        fields = '__all__'



class RequesitionerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Requesitioner
        fields = '__all__'


class PurchaseRequestSerializer(serializers.ModelSerializer):
    requisitioner = serializers.PrimaryKeyRelatedField(queryset=Requesitioner.objects.all())
    requisitioner_details = RequesitionerSerializer(source='requisitioner', read_only=True)

    campus_director = serializers.PrimaryKeyRelatedField(queryset=CampusDirector.objects.all())
    campus_director_details = CampusDirectorSerializer(source='campus_director', read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'pr_no', 
            'res_center_code', 
            'purpose', 
            'status', 
            'requisitioner', 
            'requisitioner_details', 
            'campus_director', 
            'campus_director_details', 
            'mode_of_procurement', 
            'total_amount', 
            'created_at', 
            'updated_at']  

class RequestForQoutationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RequestForQoutation
        fields = '__all__'


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


class AbstractOfQoutationSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    class Meta:
        model = AbstractOfQuotation
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
        }

     rfq_details = RequestForQoutationSerializer(source='rfq', read_only=True)



class BACMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = BACMember
        fields = '__all__' 


class SupplierSerializer(serializers.ModelSerializer):
    aoq = serializers.PrimaryKeyRelatedField(queryset=AbstractOfQuotation.objects.all(), write_only=True)
    aoq_details = AbstractOfQoutationSerializer(source='aoq', read_only=True)

    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQoutation.objects.all(), write_only=True)
    rfq_details = RequestForQoutationSerializer(source='rfq', read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

    extra_kwargs = {
            'aoq': {'write_only': True},
            'aoq_details': {'read_only': True},
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True},
        }


class SupplierItemSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all(), write_only=True)
    supplier_details = SupplierSerializer(source='supplier', read_only=True)

    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQoutation.objects.all(), write_only=True)
    rfq_details = RequestForQoutationSerializer(source='rfq', read_only=True)

    item_quotation = serializers.PrimaryKeyRelatedField(queryset=ItemQuotation.objects.all(), write_only=True)
    item_quotation_details = ItemQuotationSerializer(source='item_quotation', read_only=True)

    class Meta:
        model = SupplierItem
        fields = '__all__'

    extra_kwargs = {
            'supplier': {'write_only': True},
            'supplier_details': {'read_only': True},
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True},
            'item_quotation': {'write_only': True},
            'item_quotation_details': {'read_only': True},
        }

class PurchaseOrderSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    request_for_quotation = serializers.PrimaryKeyRelatedField(queryset=RequestForQoutation.objects.all(), write_only=True)
    rfq_details = RequestForQoutationSerializer(source='request_for_quotation', read_only=True)

    abstract_of_quotation = serializers.PrimaryKeyRelatedField(queryset=AbstractOfQuotation.objects.all(), write_only=True)
    aoq_details = AbstractOfQoutationSerializer(source='abstract_of_quotation', read_only=True)

    class Meta:
        model=PurchaseOrder
        fields = '__all__'

        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'request_for_qoutation': {'write_only': True},
            'rfq_details': {'read_only': True},
            'abstract_of_quotation': {'write_only': True},
            'aoq_details': {'read_only': True},
            
        }
        
class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    purchase_order = serializers.PrimaryKeyRelatedField(queryset=PurchaseOrder.objects.all(), write_only=True)
    pr_details = PurchaseOrderSerializer(source='purchase_order', read_only=True)
    
    supplier_item = serializers.PrimaryKeyRelatedField(queryset=SupplierItem.objects.all(), write_only=True)
    aoq_item_details = SupplierItemSerializer(source='supplier_item', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

        extra_kwargs = {
            'purchase_request': {'write_only':True},
            'pr_details': {'read_only':True},
            'purchase_order': {'write_only':True},
            'po_details': {'read_only':True},
            'supplier_item': {'write_only': True},
            'supplier_item_details': {'read_only': True},
        }

class InspectionAndAcceptanceSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    purchase_order = serializers.PrimaryKeyRelatedField(queryset=PurchaseOrder.objects.all(), write_only=True)
    po_details = PurchaseOrderSerializer(source='purchase_order', read_only=True)
    
    class Meta:
        model = InspectionAndAcceptance
        fields = '__all__'

        extra_kwargs = {
            'purchase_request': {'write_only':True},
            'pr_details': {'read_only':True},
            'purchase_order': {'write_only':True},
            'po_details': {'read_only':True},
        }

class DeliveredItemsSerializer(serializers.ModelSerializer):
    inspection = serializers.PrimaryKeyRelatedField(queryset=InspectionAndAcceptance.objects.all(), write_only=True)
    inspection_details = InspectionAndAcceptanceSerializer(source='inspection', read_only=True)

    supplier_item = serializers.PrimaryKeyRelatedField(queryset=SupplierItem.objects.all(), write_only=True)
    item_details = SupplierItemSerializer(source='supplier_item', read_only=True)

    class Meta:
        model = DeliveredItems
        fields = '__all__'

        extra_kwargs = {
            'inspection': {'write_only':True},
            'inspection_details': {'read_only':True},
            'items': {'write_only':True},
            'item_details': {'read_only':True}
        }


class RequisitionIssueSlipSerializer(serializers.ModelSerializer):

    class meta:
        model = RequisitionIssueSlip
        fields = '__all__'
