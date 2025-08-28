from django.contrib import admin

from .models import Customer, Service, Staff, Bill, BillItem,ServiceRecord , SalaryRecord

class CustomerAdmin(admin.ModelAdmin):
    list_display=('name','phone','email')

admin.site.register(Customer,CustomerAdmin)
admin.site.register(Service)
admin.site.register(Staff)
admin.site.register(Bill)
admin.site.register(BillItem)
admin.site.register(ServiceRecord)
admin.site.register(SalaryRecord)







# superuser id and password

# Userbill
# bill@123