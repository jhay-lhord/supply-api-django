from django.urls import path

from .views import *

urlpatterns = [
    path('requisitioner/', RequisitionerList.as_view()),
    path('requisitioner/<str:pk>', RequisitionerDetail.as_view()),
    path('users/', UserList.as_view()),
    path('user/<str:pk>', UserDetail.as_view()),
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
    path('abstract-of-quotation/', AbstractOfQoutationV2List.as_view()),
    path('abstract-of-quotation/<str:pk>', AbstractOfQoutationV2Detail.as_view()),
    path('item-selected-quote/', ItemSelectedForQuoteList.as_view()),
    path('item-selected-quote/<str:pk>', ItemSelectedForQuoteDetail.as_view()),
    path('purchase-order/', PurchaseOrderList.as_view()),
    path('purchase-order/<str:pk>', PurchaseOrderDetail.as_view()),
    path('inspection-report/', InspectionAcceptanceReportList.as_view()),
    path('inspection-report/<str:pk>', InspectionAcceptanceReportDetail.as_view()),
    path('requisition-slip/', RequisitionIssueSlipList.as_view()),
    path('requisition-slip/<str:pk>', RequisitionIssueSlipDetail.as_view()),

    path('daily-report/', DailyReportView.as_view()),
    path('recent-activities/', RecentActivityList.as_view(), name='recent-activities'),

]
