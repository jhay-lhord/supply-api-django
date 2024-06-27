from rest_framework import serializers

from .models import *


class ItemSerializers(serializers.ModelSerializer):

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
