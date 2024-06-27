from django.db import models


class User(models.Model):
    pass


class Item(models.Model):
    ItemNo = models.CharField(max_length=50, primary_key=True)
    Property = models.CharField(max_length=10)
    Unit = models.CharField(max_length=10)
    ItemDescription = models.CharField(max_length=50)
    Quantity = models.CharField(max_length=10)
    UnitCost = models.CharField(max_length=10)
    TotalCost = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ItemDescription


class PurchaseRequest(models.Model):
    PRNo = models.CharField(max_length=50, primary_key=True)
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    ItemNo = models.ForeignKey(Item, on_delete=models.CASCADE)
    ResCenterCode = models.CharField(max_length=10)
    Purpose = models.CharField(max_length=50)
    RequestedBy = models.CharField(max_length=50)
    ApprovedBy = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.PRNo} {self.username}'


class Supplier(models.Model):
    SupplierNo = models.CharField(max_length=50, primary_key=True)
    SupplierName = models.CharField(max_length=50)
    Tin = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.SupplierName


class PurchaseOrder(models.Model):
    PONo = models.CharField(max_length=50, primary_key=True)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    SupplierNo = models.CharField(max_length=10)
    Address = models.CharField(max_length=100)
    PlaceOfDelivery = models.CharField(max_length=100)
    DateOfDelivery = models.DateTimeField()
    DeliveryTerm = models.CharField(max_length=100)
    FundCluster = models.CharField(max_length=10)
    FundsAvailable = models.CharField(max_length=10)
    ORSBURSNo = models.CharField(max_length=10)
    DateOfORSBURS = models.DateTimeField()
    TotalAmount = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.PONo}'


class InspectionAcceptanceReport(models.Model):
    IARNo = models.CharField(max_length=50, primary_key=True)
    Supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    PurchaseOrder = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    RequisitioningOffice = models.CharField(max_length=50)
    ResCenterCode = models.CharField(max_length=10)
    # maybe create an invoice models soon
    InvoiceNo = models.CharField(max_length=10)
    DateInspected = models.DateTimeField()
    DateReceived = models.DateTimeField()
    IsInspectedAndVerified = models.CharField(max_length=10)
    IsComplete = models.CharField(max_length=10)
    IsPartial = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.IARNo} {self.ItemNo}'


class RequisitionIssueSlip(models.Model):
    RISNo = models.CharField(max_length=50, primary_key=True)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    ResCenterCode = models.CharField(max_length=10)
    Division = models.CharField(max_length=50)
    Office = models.CharField(max_length=50)
    IsStockAvailable = models.CharField(max_length=10)
    Quantity = models.CharField(max_length=10)
    Remarks = models.CharField(max_length=100)
    Purpose = models.CharField(max_length=100)
    RequestedBy = models.CharField(max_length=10)
    ApprovedBy = models.CharField(max_length=10)
    IssuedBy = models.CharField(max_length=10)
    RecievedBy = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.RISNo} {self.Office}'
