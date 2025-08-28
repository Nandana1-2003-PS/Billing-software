
from django.shortcuts import render, redirect
from .models import Customer, Service, Staff , Bill, BillItem
from django.contrib import messages 
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from django.template.loader import get_template
from django.conf import settings
from django.urls import reverse
import urllib.parse
import os
from django.utils import timezone
from .models import Customer
from datetime import datetime
from decimal import Decimal
from .models import SalaryRecord

from xhtml2pdf import pisa
from .models import Bill
from django.shortcuts import render, redirect, get_object_or_404

from django.utils.http import urlencode
from .models import Customer, Bill, BillItem, Service, Staff
from .models import ServiceRecord
from .models import Staff
from django.template.loader import render_to_string
# import weasyprint
from twilio.rest import Client

#Render Invoice as PDF
def generate_invoice_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    html_string = render_to_string('core/invoice_preview.html', {'bill': bill})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=bill_{bill.id}.pdf'
    weasyprint.HTML(string=html_string).write_pdf(response)
    return response

# # Send PDF via WhatsApp
# def send_invoice_on_whatsapp(pdf_url, customer_number):
#     client = Client(account_sid, auth_token)

#     message = client.messages.create(
#         from_='whatsapp:+14155238886',
#         body='Here is your invoice 📄',
#         media_url=[pdf_url],
#         to=f'whatsapp:{customer_number}'
#     )
#     return message.sid



from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Bill, Service, Staff  # adjust if needed
from django.utils import timezone
from datetime import datetime

from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import quote, urljoin

def create_bill(request):
    if request.method == 'POST' and request.POST.get('action') == 'save_all':
        name = request.POST['customer_name']
        phone = request.POST['customer_phone']
        email = request.POST.get('customer_email', '')
        address = request.POST.get('customer_address', '')

        dob_input = request.POST.get('customer_dob', '')
        gender = request.POST.get('customer_gender', 'O')

        try:
            dob = datetime.strptime(dob_input, '%Y-%m-%d').date() if dob_input else None
        except ValueError:
            dob = None

        
        # Save or get customer safely (avoid MultipleObjectsReturned)
        customers = Customer.objects.filter(phone=phone, name=name)

        if customers.exists():
            customer = customers.first()  # Avoid crash if duplicates
            created = False
        else:
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                dob=dob,
                gender=gender
            )
            created = True

        if not created:
            customer.email = email
            customer.address = address
            customer.dob = dob
            customer.gender = gender
            customer.save()


        # Save each service in the bill and calculate subtotal
        services = request.POST.getlist('service')
        prices = request.POST.getlist('price')
        staff_ids = request.POST.getlist('staff')

        subtotal = 0
        bill_item_data = []

        for service_id, price, staff_id in zip(services, prices, staff_ids):
            if service_id and staff_id:
                service = get_object_or_404(Service, pk=service_id)
                staff = get_object_or_404(Staff, pk=staff_id)
                price = float(price)
                subtotal += price
                bill_item_data.append((service, price, staff))

        # Discount
        discount = float(request.POST.get('discount', 0))
        amount_after_discount = subtotal - discount

        # Taxes
        cgst = round(amount_after_discount * 0.09, 2)
        sgst = round(amount_after_discount * 0.09, 2)

        # Final total
        total = round(amount_after_discount + cgst + sgst, 2)

        # Create the bill
        bill = Bill.objects.create(
            customer=customer,
            total=total,
            discount=discount,
            date=timezone.now()
        )

        # Save BillItems and ServiceRecords
        for service, price, staff in bill_item_data:
            bill.items.create(service=service, price=price, staff=staff)

            # ✅ Create corresponding ServiceRecord
            ServiceRecord.objects.create(
                staff_id=staff.id,
                staff=staff,
                customer_id=customer.id,
                customer=customer,
                service=service,
                date=bill.date  # or timezone.now().date()
            )

        # === WhatsApp Link Generation ===
        current_site = get_current_site(request)
        preview_path = reverse('invoice_pdf', kwargs={'bill_id': bill.id})
        invoice_pdf_url = request.build_absolute_uri(preview_path)

        raw_phone = customer.phone.strip().replace('+', '').replace(' ', '')
        if raw_phone.startswith('0'):
            raw_phone = '91' + raw_phone[1:]
        elif not raw_phone.startswith('91'):
            raw_phone = '91' + raw_phone

        service_names = [service.name for service, price, staff in bill_item_data]
        services_str = ', '.join(service_names)

        message = f"""Hi {customer.name}, 
        Thank you for your visit!
        Your bill is ready.
        Services: {services_str}
        Total: ₹{bill.total}
        View bill here: {invoice_pdf_url}

        - Team Salon
        """

        encoded_message = quote(message)
        whatsapp_url = f"https://wa.me/{raw_phone}?text={encoded_message}"
        request.session['whatsapp_url'] = whatsapp_url

        return redirect('invoice_preview', bill_id=bill.id)

    staff = Staff.objects.all()
    return render(request, 'core/create_bill.html', {'staff': staff})

def invoice_preview(request, bill_id):
    # Get the bill and related items
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = bill.items.all()

    # Calculate totals
    subtotal = sum(item.price for item in bill_items) - bill.discount
    cgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))
    sgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))

    # Customer details
    customer = bill.customer

    # Create services list string
    service_names = [item.service.name for item in bill_items]
    services_str = ', '.join(service_names)

    # Create invoice links
    invoice_url = request.build_absolute_uri(reverse("invoice_preview", args=[bill.id]))
    invoice_pdf_url = request.build_absolute_uri(reverse("invoice_pdf", args=[bill.id]))  # Change 'invoice_pdf' to your PDF view name

    # WhatsApp message
    message = (
        f"Hi {customer.name},\n"
        f"Thank you for your visit!\n"
        f"Your bill is ready.\n"
        f"Services: {services_str}\n"
        f"Total: ₹{bill.total}\n"
        f"View bill here: {invoice_pdf_url}\n\n"
        f"- Team Salon"
    )

    encoded_message = urllib.parse.quote(message)

    # WhatsApp URL
    phone_number = customer.phone
    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"

    # Send directly if requested
    if request.GET.get("send_whatsapp") == "true":
        return redirect(whatsapp_url)

    # Render invoice preview page
    return render(request, "core/invoice_preview.html", {
        "bill": bill,
        "bill_items": bill_items,
        "subtotal": subtotal,
        "cgst": cgst,
        "sgst": sgst,
        "send_whatsapp": False,
        "whatsapp_url": whatsapp_url,
        "redirect_url": reverse("create_bill"),
    })
def customer_list_create(request):
    if request.method == 'POST':
        name = request.POST['name']
        phone = request.POST['phone']
        email = request.POST.get('email', '')
        dob_input = request.POST.get('dob', '')
        gender = request.POST.get('gender', 'O')
        state=request.POST['state']
        district=request.POST['district']
        place=request.POST['place']
        pincode=request.POST['pincode']
        address = request.POST.get('address', '').strip()

        # Handle default values
        dob = dob_input if dob_input else timezone.now().date()
        gender = gender if gender else 'O'
        address = address if address else 'N/A'
        date=timezone.now().date()

        Customer.objects.create(
            name=name,
            phone=phone,
            email=email,
            dob=dob,
            gender=gender,
            state=state,
            district=district,
            place=place,
            pincode=pincode,
            address=address,
            date=timezone.now().date()

        )
        return redirect('customer_list_create')

    customers = Customer.objects.all()
    return render(request, 'core/customers.html', {'customers': customers})

def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        customer.name = request.POST['name']
        customer.phone = request.POST['phone']
        customer.email = request.POST.get('email', '')

        dob_input = request.POST.get('dob', '')
        gender = request.POST.get('gender', 'O')
        customer.state = request.POST['state']
        customer.district = request.POST.get('district','')
        customer.place = request.POST['place']
        customer.pincode = request.POST['pincode']
        address = request.POST.get('address', '').strip()

        customer.dob = dob_input if dob_input else timezone.now().date()
        customer.gender = gender if gender else 'O'
        customer.address = address if address else 'N/A'
        

        customer.save()
        return redirect('customer_list_create')

    return render(request, 'core/edit_customer.html', {'customer': customer})


# Delete customer
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('customer_list_create')

def customer_autocomplete(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(name__istartswith=query)[:5]

    data = [{
        'id': c.id,
        'date':c.date,
        'name': c.name,
        'phone': c.phone,
        'email': c.email or '',
        'dob': c.dob.strftime('%Y-%m-%d') if c.dob else '',
        'gender': c.gender,
        'state':c.state,
        'district':c.district,
        'place':c.place,
        'pincode':c.pincode,
        'address': c.address
        
    } for c in customers]

    return JsonResponse(data, safe=False)


#staff

def staff_list_create(request):
    if request.method == 'POST':
        name = request.POST['name']
        phone = request.POST['phone']
        email = request.POST.get('email', '')
        position = request.POST['position']
        dob_input = request.POST.get('dob', '')
        gender = request.POST.get('gender', 'O')
        address = request.POST.get('address', '').strip()
        basic_salary = request.POST['basic_salary']
        # Handle default values
        dob = dob_input if dob_input else timezone.now().date()
        gender = gender if gender else 'O'
        address = address if address else 'N/A'
        date=timezone.now().date()

        Staff.objects.create(
            name=name,
            phone=phone,
            email=email,
            position=position,

            dob=dob,
            gender=gender,
            address=address,
            basic_salary=basic_salary,
            date=timezone.now().date()
        )
        return redirect('staff_list_create')

    staffs = Staff.objects.all()
    return render(request, 'core/staffs.html', {'staffs': staffs})

def staff_update(request, pk):
    staff = get_object_or_404(Staff, pk=pk)

    if request.method == 'POST':
        staff.name = request.POST['name']
        staff.phone = request.POST['phone']
        staff.email = request.POST.get('email', '')
        staff.position = request.POST['position']
        dob_input = request.POST.get('dob', '')
        gender = request.POST.get('gender', 'O')
        address = request.POST.get('address', '').strip()
        staff.basic_salary = request.POST['basic_salary']
        staff.dob = dob_input if dob_input else timezone.now().date()
        staff.gender = gender if gender else 'O'
        staff.address = address if address else 'N/A'

        staff.save()
        return redirect('staff_list_create')

    return render(request, 'core/edit_staff.html', {'staff': staff})



# Delete Staff

def staff_delete(request, pk):
    staff_obj = get_object_or_404(Staff, pk=pk)
    staff_obj.delete()
    return redirect('staff_list_create')

def staff_autocomplete(request):
    query = request.GET.get('q', '')
    staffs = Staff.objects.filter(name__istartswith=query)[:5]

    data = [{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'email': c.email or '',
        'position': c.position,
        'dob': c.dob.strftime('%Y-%m-%d') if c.dob else '',
        'gender': c.gender,
        'address': c.address,
    } for c in staffs]

    return JsonResponse(data, safe=False)






def service_list_by_category(request):
    category = request.GET.get('category')
    services = Service.objects.filter(category=category).values('id', 'name', 'price')
    return JsonResponse(list(services), safe=False)

def service_list(request):
    from django.db.models import Prefetch

    services = Service.objects.all()
    categories = ['men', 'women', 'kids']
    services_by_category = {cat: services.filter(category=cat) for cat in categories}

    return render(request, 'core/service_list.html', {
        'services_by_category': services_by_category
    })
    
# Add service
def service_add(request):
    if request.method == 'POST':
        Service.objects.create(
            name=request.POST['name'],
            price=request.POST['price'],
            category=request.POST['category']
        )
    return redirect('service_list')

# Edit service
def service_edit(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        service.name = request.POST['name']
        service.price = request.POST['price']
        service.category = request.POST['category']
        service.save()
        return redirect('service_list')
    return render(request, 'core/service_edit.html', {'service': service})

# Delete service
def service_delete(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        service.delete()
    return redirect('service_list')




def generate_invoice(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill)
    logo_path = os.path.join(settings.BASE_DIR, '/salon_billing/core/templates/static/nibhashrdnobg.png') 

    template = get_template('core/invoice.html')
    html = template.render({
        'bill': bill,
        'bill_items': bill_items,
        'logo_path': logo_path
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=invoice_{bill.id}.pdf'
    pisa_status = pisa.CreatePDF(html, dest=response)
    return response



def invoice_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = bill.items.all()

    subtotal = sum(item.price for item in bill_items) - bill.discount
    cgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))
    sgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))

    return render(request, 'core/invoice_pdf.html', {
        'bill': bill,
        'bill_items': bill_items,
        'subtotal': subtotal,
        'cgst': cgst,
        'sgst': sgst,
    })

def invoice(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = bill.items.all()

    subtotal = sum(item.price for item in bill_items) - bill.discount
    cgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))
    sgst = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))

    return render(request, 'core/invoice_pdf.html', {
        'bill': bill,
        'bill_items': bill_items,
        'subtotal': subtotal,
        'cgst': cgst,
        'sgst': sgst,
    })

def view_billitems(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = bill.items.all()

    return render(request, 'core/view_billitems.html', {
        'bill': bill,
        'bill_items': bill_items
    })

def list_bills(request):
    
    bills = Bill.objects.select_related('customer').prefetch_related('items__service', 'items__staff')

    return render(request, 'core/list_bills.html', {'bills': bills})

def staff_performance_report(request):
    records = ServiceRecord.objects.select_related('staff', 'customer', 'service').order_by('-date')
     
    return render(request, 'core/report.html', {'records': records})





from decimal import Decimal


from django.utils.timezone import now

from calendar import month_name


MONTH_CHOICES = [
    (1, "January"),
    (2, "February"),
    (3, "March"),
    (4, "April"),
    (5, "May"),
    (6, "June"),
    (7, "July"),
    (8, "August"),
    (9, "September"),
    (10, "October"),
    (11, "November"),
    (12, "December"),
]

def monthly_salary_report(request):
    staff_list = Staff.objects.all().order_by('name')
    records = SalaryRecord.objects.select_related('staff').all().order_by('staff__name')

    return render(request, 'core/monthly_salary_report.html', {
        'staff_list': staff_list,
        'records': records,
        'months': MONTH_CHOICES, 
        'selected_month': int(request.GET.get('month', 1)),
        'selected_year': int(request.GET.get('year', 2025)),
    })


def salary_report(request):
    staff_list = Staff.objects.all().order_by('name')

    staff_data = []
    for staff in staff_list:
        basic = Decimal(staff.basic_salary or 0)

        da = basic * Decimal('0.20')
        hra = basic * Decimal('0.50')
        special_allowance = basic * Decimal('0.25')
        bonus = basic * Decimal('0.44')
        pf = basic * Decimal('0.12')
        professional_tax = Decimal('200.00')  
        salary_advance = Decimal('0.00')      

        total_gross = basic + da + hra + special_allowance + bonus
        total_deductions = pf + professional_tax + salary_advance
        net_salary = total_gross - total_deductions

        staff_data.append({
            'name': staff.name,
            'basic_salary': basic,
            'da': da,
            'hra': hra,
            'special_allowance': special_allowance,
            'bonus': bonus,
            'pf': pf,
            'professional_tax': professional_tax,
            'salary_advance': salary_advance,
            'total_gross': total_gross,
            'total_deductions': total_deductions,
            'net_salary': net_salary,
        })

    return render(request, 'core/salary_report.html', {'staff_data': staff_data})

from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def save_salary_record(request):
    if request.method == "POST":
        try:
            staff_id = request.POST.get("staff_id")
            staff = Staff.objects.get(id=staff_id)
            unpaid_leave=int(request.POST.get("unpaid_leave", 0) or 0)
            bonus = float(request.POST.get("bonus", 0) or 0)
            pf = float(request.POST.get("pf", 0) or 0)
            esi = float(request.POST.get("esi", 0) or 0)
            advance = float(request.POST.get("advance", 0) or 0)

            # Store actual DB fields, including ESI
            SalaryRecord.objects.create(
                staff=staff,
                unpaid_leave=unpaid_leave,
                bonus=bonus,
                pf=pf,
                esi=esi,
                salary_advance=advance
            )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


def base(request):
    return render(request, 'core/base.html')

def dashboard(request):
    return render(request, 'core/dashboard.html')

def salary_slip_preview(request, record_id):
    """Preview salary slip in browser."""
    record = get_object_or_404(SalaryRecord.objects.select_related("staff"), id=record_id)

    # Generate WhatsApp message text
    staff = record.staff
    message = (
        f"Hi {staff.name},\n"
        f"Your salary slip for {record.date.strftime('%B %Y')} is ready.\n"
        f"Net Salary: ₹{record.net_salary}\n"
        f"View Slip: {request.build_absolute_uri(reverse('salary_slip_preview', args=[record.id]))}\n\n"
        f"- HR Team"
    )
    encoded_message = urllib.parse.quote(message)
    phone = staff.phone.strip().replace(" ", "").replace("+", "")
    if not phone.startswith("91"):  # default India
        phone = "91" + phone

    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"

    return render(request, "core/salary_slip_preview.html", {
        "record": record,
        "whatsapp_url": whatsapp_url,
    })


def salary_slip_send_whatsapp(request, record_id):
    """Redirect directly to WhatsApp with salary slip message."""
    record = get_object_or_404(SalaryRecord.objects.select_related("staff"), id=record_id)
    staff = record.staff

    message = (
        f"Hi {staff.name},\n"
        f"Your salary slip for {record.date.strftime('%B %Y')} is ready.\n"
        f"Net Salary: ₹{record.net_salary}\n"
        f"View Slip: {request.build_absolute_uri(reverse('salary_slip_preview', args=[record.id]))}\n\n"
        f"- HR Team"
    )
    encoded_message = urllib.parse.quote(message)

    phone = staff.phone.strip().replace(" ", "").replace("+", "")
    if not phone.startswith("91"):  # default India
        phone = "91" + phone

    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
    return redirect(whatsapp_url)

def salary_pdf(request, record_id):
    record = get_object_or_404(SalaryRecord, pk=record_id)
    return render(request, "core/salary_pdf.html", {"record": record})