from django.contrib.auth.models import User
from django.db import models


class Item(models.Model):
    item_no = models.CharField(max_length=50, primary_key=True)
    item_property = models.CharField(max_length=10)
    unit = models.CharField(max_length=10)
    item_description = models.CharField(max_length=50)
    quantity = models.CharField(max_length=10)
    unit_cost = models.CharField(max_length=10)
    total_cost = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_description


class PurchaseRequest(models.Model):
    pr_no = models.CharField(max_length=50, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_no = models.ForeignKey(Item, on_delete=models.CASCADE)
    res_center_code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)
    requested_by = models.CharField(max_length=50)
    approved_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.pr_no} {self.user.username}'


class Supplier(models.Model):
    supplier_no = models.CharField(max_length=50, primary_key=True)
    supplier_name = models.CharField(max_length=50)
    tin = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name


class PurchaseOrder(models.Model):
    po_no = models.CharField(max_length=50, primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    supplier_no = models.CharField(max_length=10)
    address = models.CharField(max_length=100)
    place_of_delivery = models.CharField(max_length=100)
    date_of_delivery = models.DateTimeField()
    delivery_term = models.CharField(max_length=100)
    fund_cluster = models.CharField(max_length=10)
    funds_available = models.CharField(max_length=10)
    orsburs_no = models.CharField(max_length=10)
    date_of_orsburs = models.DateTimeField()
    total_amount = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.po_no}'


class InspectionAcceptanceReport(models.Model):
    iar_no = models.CharField(max_length=50, primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    requisitioning_office = models.CharField(max_length=50)
    res_center_ode = models.CharField(max_length=10)
    # maybe create an invoice models soon
    invoice_no = models.CharField(max_length=10)
    date_inspected = models.DateTimeField()
    date_received = models.DateTimeField()
    is_inspected_and_verified = models.CharField(max_length=10)
    is_complete = models.CharField(max_length=10)
    is_partial = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.iar_no} {self.item_no}'


class RequisitionIssueSlip(models.Model):
    ris_no = models.CharField(max_length=50, primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    res_center_code = models.CharField(max_length=10)
    division = models.CharField(max_length=50)
    office = models.CharField(max_length=50)
    is_stock_available = models.CharField(max_length=10)
    quantity = models.CharField(max_length=10)
    remarks = models.CharField(max_length=100)
    purpose = models.CharField(max_length=100)
    requested_by = models.CharField(max_length=10)
    approved_by = models.CharField(max_length=10)
    issued_by = models.CharField(max_length=10)
    recieved_by = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.ris_no} {self.office}'
