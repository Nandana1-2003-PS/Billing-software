import pywhatkit as kit
import pandas as pd
from twilio.rest import Client
from datetime import datetime
import schedule
import time

# Twilio credentials
ACCOUNT_SID = 'YOUR_TWILIO_SID'
AUTH_TOKEN = 'YOUR_TWILIO_AUTH'
TWILIO_NUMBER = '+1234567890'  # Your Twilio number
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Time to send messages (24-hour format)
SEND_HOUR = 14
SEND_MINUTE = 24

def send_wishes():
    today = datetime.now().strftime("%Y-%m-%d")
    birthdays = pd.read_csv("birthdays.csv")

    for _, row in birthdays.iterrows():
        if row['date'] == today:
            name = row['name']
            phone = row['phone']
            message = f"🎉 Happy Birthday {name}! Wishing you a fantastic day! 🎂"

            # Send WhatsApp message
            try:
                kit.sendwhatmsg(phone, message, SEND_HOUR, SEND_MINUTE)
                print(f"WhatsApp message scheduled for {name}")
            except Exception as e:
                print(f"Failed to send WhatsApp message to {name}: {e}")

            # Send SMS message
            try:
                sms = client.messages.create(
                    body=message,
                    from_=TWILIO_NUMBER,
                    to=phone
                )
                print(f"SMS sent to {name}")
            except Exception as e:
                print(f"Failed to send SMS to {name}: {e}")

# Schedule to run daily at SEND_HOUR:SEND_MINUTE
schedule.every().day.at(f"{SEND_HOUR:02d}:{SEND_MINUTE:02d}").do(send_wishes)

print("Birthday scheduler started...")
while True:
    schedule.run_pending()
    time.sleep(30)
