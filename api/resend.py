import os

import resend
from django.core.mail import send_mail
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ['RESEND_API_KEY']

sender_domain_name = os.environ['DOMAIN_NAME']


def send_mail_resend(reciever, subject, html):
    params = {'from': f'supply-office@{sender_domain_name}', 'to': [reciever], 'subject': subject, 'html': html}
    email = resend.Emails.send(params)
    return email


def send_mail_django(message, subject, email):
    send_mail(subject, message, 'settings.EMAIL_HOST_USER', [email], fail_silently=False)
