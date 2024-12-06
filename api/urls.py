from django.urls import path

from .views import *

urlpatterns = [
    path('requisitioner/', RequisitionerList.as_view()),
    path('requisitioner/<str:pk>', RequisitionerDetail.as_view()),

    path('users/', UserList.as_view()),
    path('user/<str:pk>', UserDetail.as_view()),
    path('users/<int:pk>/edit/', EditUserView.as_view()),

    path('campus-director/', CampusDirectorList.as_view()),
    path('campus-director/<str:pk>', CampusDirectorDetail.as_view()),

    path('bac-member/', BACMemberList.as_view()),
    path('bac-member/<str:pk>', BACMemberDetail.as_view()),

    path('item/', ItemList.as_view()),
    path('item/<str:pk>', ItemDetail.as_view()),
    path('item/<str:field_name>/<str:value>/', ItemsDetail.as_view()),

    path('purchase-request/', PurchaseRequestList.as_view()),
    path('purchase-request/<str:pk>', PurchaseRequestDetail.as_view()),

    path('request-for-qoutation/', RequestForQoutationList.as_view()),
    path('request-for-qoutation/<str:pk>', RequestForQoutationDetail.as_view()),

    path('item-quotation/', ItemQuotationList.as_view()),
    path('item-quotation/<str:pk>', ItemQuotationDetail.as_view()),

    path('abstract-of-quotation/', AbstractOfQoutationList.as_view()),
    path('abstract-of-quotation/<str:pk>', AbstractOfQoutationDetail.as_view()),

    path('item-selected-quote/', ItemSelectedForQuoteList.as_view()),
    path('item-selected-quote/<str:pk>', ItemSelectedForQuoteDetail.as_view()),

    path('purchase-order/', PurchaseOrderList.as_view()),
    path('purchase-order/<str:pk>', PurchaseOrderDetail.as_view()),
    path('purchase-order/<str:pk>/update-status/', PurchaseOrderStatusUpdateView.as_view()),

    path('purchase-order-item/', PurchaseOrderItemList.as_view()),
    path('purchase-order-item/<str:pk>', PurchaseOrderItemDetail.as_view()),

    path('items-delivered/', DeliveredItemsList.as_view()),
    path('items-delivered/<str:pk>', DeliveredItemsDetail.as_view()),

    path('inspection-report/',InspectionAndAcceptanceList.as_view()),
    path('inspection-report/<str:pk>', InspectionAndAcceptanceDetail.as_view()),
    
    path('requisition-slip/', RequisitionIssueSlipList.as_view()),
    path('requisition-slip/<str:pk>', RequisitionIssueSlipDetail.as_view()),

    path('daily-report/bac', BACDailyReportView.as_view()),
    path('daily-report/supply', SupplyDailyReportView.as_view()),
    path('recent-activities/', RecentActivityList.as_view(), name='recent-activities'),

]
