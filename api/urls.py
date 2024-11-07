from django.urls import path

from .views import *

urlpatterns = [
    path('users/', UserList.as_view()),
    path('user/<str:pk>', UserDetail.as_view()),
    path('item/', ItemList.as_view()),
    path('item/<str:pk>', ItemDetail.as_view()),
    path('item/<str:field_name>/<str:value>/', ItemsDetail.as_view()),
    path('purchase-request/', PurchaseRequestList.as_view()),
    path('purchase-request/<str:pk>', PurchaseRequestDetail.as_view()),
    path('request-for-qoutation/', RequestForQoutationList.as_view()),
    path('request-for-qoutation/<str:pk>', RequestForQoutationDetail.as_view()),
    path('purchase-order/', PurchaseOrderList.as_view()),
    path('purchase-order/<str:pk>', PurchaseOrderDetail.as_view()),
    path('inspection-report/', InspectionAcceptanceReportList.as_view()),
    path('inspection-report/<str:pk>', InspectionAcceptanceReportDetail.as_view()),
    path('requisition-slip/', RequisitionIssueSlipList.as_view()),
    path('requisition-slip/<str:pk>', RequisitionIssueSlipDetail.as_view()),
]
