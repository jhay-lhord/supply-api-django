from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.response import Response

from .models import *

User = get_user_model()
class CreateUserSerializer(serializers.ModelSerializer):
    print('serializer started')
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        print('validated')
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Password fields didn\'t match.'})
        return attrs

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(
            first_name = first_name,
            last_name = last_name,
            email = email,
            password = password
        )
        user.is_active = False
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create(**validated_data)
        print(user)
        return user


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = '__all__'


class PurchaseRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseRequest
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
