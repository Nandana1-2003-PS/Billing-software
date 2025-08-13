# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from core.models import Customer, Staff  # Adjust if app is not named 'core'
# from urllib.parse import quote
# import webbrowser

# class Command(BaseCommand):
#     help = 'Send WhatsApp birthday wishes to customers and staff'

#     def handle(self, *args, **kwargs):
#         today = timezone.now().date()

#         birthday_people = list(Customer.objects.filter(dob__month=today.month, dob__day=today.day)) + \
#                           list(Staff.objects.filter(dob__month=today.month, dob__day=today.day))

#         for person in birthday_people:
#             if person.phone:
#                 phone = person.phone.strip().replace('+', '').replace(' ', '')
#                 if phone.startswith('0'):
#                     phone = '91' + phone[1:]
#                 elif not phone.startswith('91'):
#                     phone = '91' + phone

#                 message = f"Hi {person.name}, 🎉\nHappy Birthday! 🎂\n– Team Salon 💇‍♀️"
#                 encoded = quote(message)
#                 url = f"https://wa.me/{phone}?text={encoded}"
#                 webbrowser.open(url)

#                 self.stdout.write(self.style.SUCCESS(f"Prepared message for {person.name}"))
import pywhatkit as kit
kit.sendwhatmsg_istantly("+919048796753", "Hello from Python!")