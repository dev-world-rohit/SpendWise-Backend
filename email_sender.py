import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()


def send_mail(email, email_send):
    sender_email = os.getenv("EMAIL")
    receiver_email = email
    message = EmailMessage()
    message["Subject"] = "OTP from Spendwise"
    message["From"] = sender_email
    message["To"] = receiver_email

    # encoded = base64.b64encode(open("mailtrap.jpg", "rb").read()).decode()
    email_to_send = email_send
    message.set_content(email_to_send, subtype='html')

    with smtplib.SMTP(host='smtp.gmail.com', port=587, timeout=120) as connection:
        connection.starttls()
        connection.login(user=sender_email, password=os.getenv("PASSWORD"))
        connection.sendmail(sender_email,
                            receiver_email,
                            msg=message.as_string())
