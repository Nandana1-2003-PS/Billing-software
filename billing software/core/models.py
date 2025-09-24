from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.utils.timezone import now
from django.contrib.auth.models import User

from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password

class Log(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=256)  # hashed password

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    dob = models.DateField(default=timezone.now)
    address = models.TextField(default='N/A')
    state = models.CharField(max_length=100,null=True)
    district = models.CharField(max_length=100,null=True)
    place = models.CharField(max_length=100,null=True)
    pincode = models.CharField(max_length=6,null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F')
    
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.date}"
    

class Service(models.Model):
    CATEGORY_CHOICES = (
        ('men', 'Men'),
        ('women', 'Women'),
        ('kids', 'Kids'),
    )

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.category})"



class Staff(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    position = models.CharField(max_length=100,null=True, blank=True)
    dob = models.DateField(default=timezone.now)
    address = models.TextField(default='N/A')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F')
    date = models.DateField(default=timezone.now)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
    
class ServiceRecord(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.staff.name} served {self.customer.name} for {self.service.name} on {self.date}"



class Bill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Bill #{self.id} - {self.customer.name}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)


from decimal import Decimal
from django.db import models
from django.utils.timezone import now

class SalaryRecord(models.Model):
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, help_text="Select a staff member")
    unpaid_leave = models.IntegerField("Unpaid Leave (Days)", default=0)
    month = models.IntegerField("Month", default=now().month)
    year = models.IntegerField("Year", default=now().year)

    bonus = models.DecimalField("Bonus", max_digits=10, decimal_places=2, default=0)

    pf_percent = models.DecimalField("PF (%)", max_digits=5, decimal_places=2, blank=True, null=True,
                                     help_text="Enter PF percentage (optional, e.g. 12 for 12%)")
    esi_percent = models.DecimalField("ESI (%)", max_digits=5, decimal_places=2, blank=True, null=True,
                                      help_text="Enter ESI percentage (optional, e.g. 1.75 for 1.75%)")

    pf = models.DecimalField("PF Amount", max_digits=10, decimal_places=2, blank=True, null=True, editable=False)
    esi = models.DecimalField("ESI Amount", max_digits=10, decimal_places=2, blank=True, null=True, editable=False)

    salary_advance = models.DecimalField("Salary Advance", max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        basic = Decimal(self.staff.basic_salary or 0)

        # PF calculation
        if self.pf_percent:
            self.pf = (basic * Decimal(self.pf_percent)) / Decimal(100)
        else:
            self.pf = Decimal(0)

        # ESI calculation
        if self.esi_percent:
            self.esi = (basic * Decimal(self.esi_percent)) / Decimal(100)
        else:
            self.esi = Decimal(0)

        super().save(*args, **kwargs)

    @property
    def per_day_salary(self):
        basic = Decimal(self.staff.basic_salary or 0)
        return basic / Decimal(30)

    @property
    def unpaid_leave_deduction(self):
        return self.per_day_salary * Decimal(self.unpaid_leave or 0)

    @property
    def total_gross(self):
        basic = Decimal(self.staff.basic_salary or 0)
        return basic + Decimal(self.bonus or 0) - Decimal(self.unpaid_leave_deduction or 0)

    @property
    def total_deductions(self):
        return Decimal(self.pf or 0) + Decimal(self.esi or 0) + Decimal(self.salary_advance or 0)

    @property
    def net_salary(self):
        return self.total_gross - self.total_deductions

    def __str__(self):
        return f"{self.staff.name} - {self.date}"



class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=50, default="pcs")  # e.g., pcs, ml, g
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_quantity = models.PositiveIntegerField(default=0, help_text="Reorder level")

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        stock_in = self.stockins.aggregate(models.Sum("quantity"))["quantity__sum"] or 0
        stock_out = self.stockouts.aggregate(models.Sum("quantity"))["quantity__sum"] or 0
        return stock_in - stock_out


class StockIn(models.Model):
    product = models.ForeignKey(Product, related_name="stockins", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    supplier = models.CharField(max_length=200, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} +{self.quantity} on {self.date}"


class StockOut(models.Model):
    product = models.ForeignKey(Product, related_name="stockouts", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    reason = models.CharField(
        max_length=100,
        choices=[
            ("sale", "Sale"),
            ("service", "Service Use"),
            ("wastage", "Wastage"),
            ("other", "Other"),
        ],
        default="sale",
    )
    bill_item = models.ForeignKey("BillItem", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} -{self.quantity} on {self.date} ({self.reason})"