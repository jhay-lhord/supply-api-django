import os

import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ['RESEND_API_KEY']

sender_domain_name = os.environ['DOMAIN_NAME']


def send_mail(reciever, subject, html):
    params = {'from': f'email@{sender_domain_name}', 'to': [reciever], 'subject': subject, 'html': html}
    email = resend.Emails.send(params)
    return email

def send_OTP_mail(reciever, subject, html):
    params = {'from': f'noreply@{sender_domain_name}', 'to': [reciever], 'subject': subject, 'html': html}
    email = resend.Emails.send(params)
    print(f'OTP email sucessfully sent')
    return email
