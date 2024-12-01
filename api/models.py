import pyotp
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class CustomUserManager(BaseUserManager):

    def create(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Ensure is_superuser and is_staff are True for superuser
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        # Create a new superuser
        return self.create(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=10, null=True, blank=True)
    otp_expiration = models.DateTimeField(null=True, blank=True)
    otp_secret = models.CharField(max_length=32, null=True, blank=True)

    # Specify the custom user manager
    objects = CustomUserManager()

    # Set username to None to effectively ignore it
    username = None

    # Set the email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def generate_otp(self):
        """Generates OTP and sets expiration time."""
        totp = pyotp.TOTP(self.otp_secret)
        self.otp_code = totp.now()
        self.otp_expiration = timezone.now() + timezone.timedelta(minutes=5)
        self.save()
        return self.otp_code

    def verify_otp(self, otp_code):
        """Verifies the OTP code and checks its expiration."""
        if self.otp_code == otp_code and timezone.now() < self.otp_expiration:
            # Clear the OTP after verification
            self.otp_code = None
            self.otp_expiration = None
            self.save()
            return True
        return False

    
class RecentActivity(models.Model):
    ACTIVITY_TYPES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} {self.get_activity_type_display()} {self.content_type}"


class PurchaseRequest(models.Model):
    pr_no = models.CharField(max_length=50, primary_key=True)
    res_center_code = models.CharField(max_length=50)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default='pending')
    requested_by = models.CharField(max_length=255)
    approved_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.pr_no}'

class Item(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, related_name="items", on_delete=models.CASCADE)
    item_no = models.CharField(primary_key=True)
    stock_property_no = models.CharField(max_length=20)
    unit = models.CharField(max_length=255)
    item_description = models.CharField(max_length=255)
    quantity = models.CharField(max_length=50)
    unit_cost = models.CharField(max_length=50)
    total_cost = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_description


class RequestForQoutation(models.Model):
    rfq_no = models.CharField(max_length=50, primary_key=True)
    supplier_name = models.CharField(max_length=255)
    supplier_address = models.CharField(max_length=255)
    tin = models.CharField(max_length=50, null=True, blank=True)
    is_VAT = models.BooleanField(default=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Qoutation: {self.qoutation_no}'

class ItemQuotation(models.Model):
    item_quotation_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    rfq = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit_price = models.CharField(max_length=255)
    brand_model = models.CharField(max_length=255)
    is_low_price = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Item Quotation: {self.rfq}'

class AbstractOfQoutation(models.Model):
    afq_no = models.CharField(max_length=50, primary_key=True)
    rfq = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Abstract of Qoutation for {self.purchase_request} of {self.purchase_request.user}'


class AbstractOfQuotationV2(models.Model):
    aoq_no = models.CharField(primary_key=True)
    rfq = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    item_quotation = models.ForeignKey(ItemQuotation, on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Abstract of Qoutation for {self.purchase_request} of {self.purchase_request.user}'


class ItemSelectedForQuote(models.Model):
    item_selected_no = models.CharField(max_length=50, primary_key=True)
    aoq = models.ForeignKey(AbstractOfQuotationV2, on_delete=models.CASCADE)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    rfq = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
    item_qoutation = models.ForeignKey(ItemQuotation, on_delete=models.CASCADE)
    is_item_selected = models.BooleanField(default=False)
    total_amount = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrder(models.Model):
    po_no = models.CharField(primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    request_for_qoutation = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
    total_amount = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.po_no}'



class Supplier(models.Model):
    supplier_no = models.CharField(max_length=50, primary_key=True)
    supplier_name = models.CharField(max_length=50)
    tin = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name


class InspectionAcceptanceReport(models.Model):
    iar_no = models.CharField(max_length=50, primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
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
        return f'{self.iar_no}' 


class RequisitionIssueSlip(models.Model):
    ris_no = models.CharField(max_length=50, primary_key=True)
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


class Budget(models.Model):
    budget_no = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    budget_allocation = models.CharField(max_length=20)

    def __str__(self):
        return f'Budget: {self.budget_allocation}'


class Bidding(models.Model):
    bidding_no = models.CharField(max_length=50)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_amount = models.CharField(max_length=50)

    def __str__(self):
        return f'Bidding: Supplier({self.supplier}) with the total amount of {self.total_amount}'


class Requesitioner(models.Model):
    requisition_id = models.CharField(primary_key=True)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

class CampusDirector(models.Model):
    cd_id = models.CharField(primary_key=True)
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class BACMember(models.Model):
    member_id = models.CharField(primary_key=True)
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


# class RecentActivity(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
#     purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)

#     def __str__(self):
#         return f'User Activity: {self.purchase_request}, {self.purchase_order}'


# Dashboard
# class InventoryManagement(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
#     purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

#     def __str__(self):
#         return f'User Inventory: {self.purchase_order}'


# class SupplyDashboardManagement(models.Model):
#     purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
#     purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
#     qoutation = models.ForeignKey(AbstractOfQoutation, on_delete=models.CASCADE)

#     def __str__(self):
#         return f'{self.purchase_request}, {self.purchase_order}, {self.qoutation}'


# class BudgetDashboardManagement(models.Model):
#     budget = models.ForeignKey(Budget, on_delete=models.CASCADE)

#     def __str__(self):
#         return f' Budget: {self.budget}'


# class BACDashboardManagement(models.Model):
#     request_for_qoutation = models.ForeignKey(RequestForQoutation, on_delete=models.CASCADE)
#     abstract_of_qoutation = models.ForeignKey(AbstractOfQoutation, on_delete=models.CASCADE)

#     def __str__(self):
#         return f'{self.request_for_qoutation}, {self.abstract_of_qoutation}'
