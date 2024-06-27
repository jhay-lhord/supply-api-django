from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *


class ItemList(generics.ListCreateAPIView):
    """
    List all Item, or create a new item
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializers
    permission_class = [IsAuthenticated]


class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Item instance
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializers
    permission_class = [IsAuthenticated]


class PurchaseRequestList(generics.ListCreateAPIView):
    """
    List all Purchase request, or create a new Purchase request
    """
    queryset = PurchaseRequest.objects.select_related('User').all()
    serializer_class = PurchaseRequestSerializer
    permission_class = [IsAuthenticated]


class PurchaseRequestDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase request instance
    """
    queryset = PurchaseRequest.objects.select_related('User').all()
    serializer_class = PurchaseRequestSerializer
    permission_class = [IsAuthenticated]


class SupplierList(generics.ListCreateAPIView):
    """
    List all Supplier, or create a new Supplier
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_class = [IsAuthenticated]


class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Supplier instance
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_class = [IsAuthenticated]


class PurchaseOrderList(generics.ListCreateAPIView):
    """
    List all Purchase Order, or create a new Purchase Order
    """
    queryset = PurchaseOrder.objects.select_related('Item').all()
    serializer_class = PurchaseOrderSerializer
    permission_class = [IsAuthenticated]


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Purchase Order instance
    """
    queryset = PurchaseOrder.objects.select_related('Item').all()
    serializer_class = PurchaseOrderSerializer
    permission_class = [IsAuthenticated]


class InspectionAcceptanceReportList(generics.ListCreateAPIView):
    """
    List all  Inspection report , or create a new Inspection report
    """
    queryset = InspectionAcceptanceReport.objects.select_related('Supplier', 'Item', 'PurchaseOrder').all()
    serializer_class = InspectionAcceptanceReportSerializer
    permission_class = [IsAuthenticated]


class InspectionAcceptanceReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Inspection report instance
    """
    queryset = InspectionAcceptanceReport.objects.select_related('Supplier', 'Item', 'PurchaseOrder').all()
    serializer_class = InspectionAcceptanceReportSerializer
    permission_class = [IsAuthenticated]


class RequisitionIssueSlipList(generics.ListCreateAPIView):
    """
    List all  Requisition Slip , or create a new  Requisition Slip
    """
    queryset = RequisitionIssueSlip.objects.select_related('Item').all()
    serializer_class = RequisitionIssueSlipSerializer
    permission_class = [IsAuthenticated]


class RequisitionIssueSlipDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update or Delete a Requisition Slip instance
    """
    queryset = RequisitionIssueSlip.objects.all()
    serializer_class = RequisitionIssueSlipSerializer
    permission_class = [IsAuthenticated]
