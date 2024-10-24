from django.urls import path

from .views import *

urlpatterns = [
    path('users/', UserList.as_view()),
    path('user/<str:pk>', UserDetail.as_view()),
    path('item/', ItemList.as_view()),
    path('item/<str:pk>', ItemDetail.as_view()),
    path('purchase-request/', PurchaseRequestList.as_view()),
    path('purchase-request/<str:pk>', PurchaseRequestDetail.as_view()),
    path('supplier/', SupplierList.as_view()),
    path('supplier/<str:pk>', SupplierDetail.as_view()),
    path('purchase-order/', PurchaseOrderList.as_view()),
    path('purchase-order/<str:pk>', PurchaseOrderDetail.as_view()),
    path('inspection-report/', InspectionAcceptanceReportList.as_view()),
    path('inspection-report/<str:pk>', InspectionAcceptanceReportDetail.as_view()),
    path('requisition-slip/', RequisitionIssueSlipList.as_view()),
    path('requisition-slip/<str:pk>', RequisitionIssueSlipDetail.as_view()),
    path('purchase-request-item/', PurchaseRequestItemList.as_view()),
]
