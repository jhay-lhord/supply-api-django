from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import pyotp


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
    otp_code = models.CharField(null=True, blank=True)
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
        return f'{str(self.id)} - {self.email}'

    def generate_otp(self):
        """Generates OTP and sets expiration time."""
        totp = pyotp.TOTP(self.otp_secret)
        self.otp_code = totp.now()
        self.otp_expiration = timezone.now() + timezone.timedelta(minutes=5)
        self.save()
        print(f'The OTP is generate successfully: {self.otp_code}')
        return self.otp_code

    def verify_otp(self, otp_code):
        """Verifies the OTP code and checks its expiration."""
        if self.otp_code == otp_code and timezone.now() < self.otp_expiration:
            # Clear the OTP after verification
            self.otp_code = None
            self.otp_expiration = None
            self.save()
            print(f'The OTP is successfully verify')
            return True
        return False


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
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
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
