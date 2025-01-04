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
    

def send_file(file, email, html):
    """
    Sends an email with a file attachment using the Resend API.

    Args:
        file (InMemoryUploadedFile or file-like object): The file to be attached.
        email (str): The recipient's email address.

    Returns:
        dict: A response indicating success or failure.
    """
    if not email or not file:
        return {"error": "Both email and file are required."}

    # Save the uploaded file temporarily
    temp_file_path = os.path.join("temp", file.name)
    os.makedirs("temp", exist_ok=True)  # Ensure the temp directory exists

    try:
        with open(temp_file_path, "wb") as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        # Prepare the file as an attachment
        with open(temp_file_path, "rb") as f:
            file_content = f.read()

        attachment = {
            "content": list(file_content),
            "filename": file.name,
        }

        # Prepare email parameters
        params = {
            "from": f'supply-office@{sender_domain_name}',
            "to": [email],
            "subject": "Your File Attachment",
            "html": html,
            "attachments": [attachment],
        }

        # Send the email using Resend
        resend.Emails.send(params)

        return {"message": "Email sent successfully."}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

