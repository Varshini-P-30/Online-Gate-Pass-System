import os
from twilio.rest import Client

def send_sms_via_twilio(to_number, message_body):
    """
    Sends an SMS message to a parent's phone number using Twilio.
    Each student's parent number is handled individually.
    """

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')

    # 🧠 Validate credentials
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials! Check .env or environment variables.")
        return False

    # ✅ Create Twilio client
    client = Client(account_sid, auth_token)

    # 📞 Ensure Indian number has proper prefix
    if not to_number.startswith('+'):
        to_number = f'+91{to_number.strip()}'

    try:
        # 🚀 Send SMS
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        print(f"✅ SMS sent successfully to {to_number}. SID: {message.sid}")
        return True

    except Exception as e:
        print(f"❌ Failed to send SMS to {to_number}: {e}")
        return False
