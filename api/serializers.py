from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import *

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Password fields didnt match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(email=validated_data['email'], password=validated_data['password'])
        user.is_active = False
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
