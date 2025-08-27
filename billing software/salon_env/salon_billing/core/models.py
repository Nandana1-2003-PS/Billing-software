from django.db import models
from django.utils import timezone
from decimal import Decimal

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


class SalaryRecord(models.Model):
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE)
    unpaid_leave= models.IntegerField("Unpaid Leave(Days)", default=0)
    bonus = models.DecimalField("Bonus", max_digits=10, decimal_places=2, default=0)  # Editable
    pf = models.DecimalField("PF 12%", max_digits=10, decimal_places=2, blank=True, null=True)
    esi = models.DecimalField("ESI 1.75%", max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    
    salary_advance = models.DecimalField("Salary Advance", max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Auto-calculate PF and ESI from basic salary if not provided."""
        if self.staff:
            basic = Decimal(self.staff.basic_salary or 0)
            
            self.pf = basic * Decimal('0.12')
            self.esi = basic * Decimal('0.0175')
        super().save(*args, **kwargs)

    @property
    def per_day_salary(self):
        """Calculate per-day salary from basic (assuming 30 days in a month)."""
        basic = Decimal(self.staff.basic_salary or 0)
        return basic / Decimal(30)

    @property
    def unpaid_leave_deduction(self):
        """Deduction for unpaid leave days."""
        return self.per_day_salary * (self.unpaid_leave or 0)

    @property
    def total_gross(self):
        """Gross salary = Basic + Bonus - Unpaid leave deduction"""
        basic = Decimal(self.staff.basic_salary or 0)
        return basic + (self.bonus or 0) - (self.unpaid_leave_deduction or 0)

    @property
    def total_deductions(self):
        """Total deductions = PF + ESI + Advance  """
        return (self.pf or 0) + (self.esi or 0) + (self.salary_advance or 0) 

    @property
    def net_salary(self):
        """Net salary = Gross - Deductions"""
        return self.total_gross - self.total_deductions

    def __str__(self):
        return f"{self.staff.name} - {self.date}"