from celery import shared_task
from datetime import date
from .models import Customer
from django.urls import reverse
from urllib.parse import urlencode
import requests

@shared_task
def send_birthday_messages():
    today = date.today()
    customers = Customer.objects.filter(dob__month=today.month, dob__day=today.day)

    for customer in customers:
        message = (
            f"🎉 Happy Birthday, {customer.name}! 🎂\n"
            f"Wishing you a beautiful day filled with love and celebration.\n\n"
            f"– Your Salon Team 💇"
        )

        phone = customer.phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = phone[1:]
        if not phone.startswith("91"):
            phone = "91" + phone

        whatsapp_url = f"https://wa.me/{phone}?text={urlencode({'': message})[1:]}"
        
        # Optionally, you could use Twilio to send the message directly.
        print(f"Send WhatsApp to {phone}: {whatsapp_url}")
