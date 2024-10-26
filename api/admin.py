from django.contrib import admin

from .models import *

admin.site.register(CustomUser)
admin.site.register(Item)
admin.site.register(PurchaseRequest)
admin.site.register(Supplier)
admin.site.register(PurchaseOrder)
admin.site.register(InspectionAcceptanceReport)
admin.site.register(RequisitionIssueSlip)
