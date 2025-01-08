from django_filters import rest_framework as filters
from .models import *

class ItemsFilter(filters.FilterSet):
    pr_no = filters.CharFilter(field_name='purchase_request__pr_no', lookup_expr='exact')

    class Meta:
        model = Item
        fields = ['purchase_request',]
        
        
class DeliveredItemsFilter(filters.FilterSet):
    pr_no = filters.CharFilter(field_name='purchase_request__pr_no', lookup_expr='exact')

    class Meta:
        model = DeliveredItems
        fields = ['purchase_request',]
        
        
class TrackStatusFilter(filters.FilterSet):
    pr_no = filters.CharFilter(field_name='pr_no__pr_no', lookup_expr='exact')

    class Meta:
        model = TrackStatus
        fields = ['pr_no',]
