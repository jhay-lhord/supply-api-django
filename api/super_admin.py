import pyotp
from .models import CustomUser
from dotenv import load_dotenv
from django.contrib.auth import get_user_model
import uuid
import os
from .resend import send_mail_resend
from .groups import assign_role_and_save

load_dotenv()
User = get_user_model()
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')


def create_super_admin_user():
    first_name = os.getenv("ADMIN_FIRST_NAME")
    last_name = os.getenv("ADMIN_LAST_NAME")
    email = os.getenv("ADMIN_EMAIL")
    password = generate_password()

    if not CustomUser.objects.filter(email=email).exists():
        admin_user = User.objects.create(
          first_name = first_name,
          last_name = last_name,
          email = email,
          password = password,
          is_active = True,
          is_staff = True,
          is_superuser = True,
        )
        admin_user.otp_secret = pyotp.random_base32()

        admin_user.set_password(password)

        assign_role_and_save(admin_user, 'Admin')

        admin_user.save()

        subject = "Admin Account Successfully Created"
        message = f"""     
        <html>
        <head>
            <style>                
                body {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{
                        width: 100% !important;
                        padding: 10px !important;


                    }}
                    .header, .footer {{
                        padding: 15px !important;
                    }}
                    .cta-button {{
                        width: 100% !important;
                        display: block !important;
                        font-size: 14px !important;
                        padding: 10px 0 !important;
                    }}
                    .content-box {{
                        padding: 10px !important;
                    }}
                    .text {{
                        font-size: 16px !important;
                    }}
                }}
            </style>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f5f5f5; margin: 0;">
            <div class="container" style=" width: 100%; margin: auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);">
                
                <!-- Header Section -->
                <div class="header" style="background-color: #fdba74; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 24px; margin: 0;">Supply Office</h1>
                    <p style="color: #ffffff; font-size: 14px; margin: 0;">Your Admin Account Has Been Created!</p>
                </div>

                <!-- Body Section -->
                <div class="content-box" style="padding: 30px 20px;">
                    <p class="text" style="font-size: 18px; color: #333; margin-top: 0;">Hi {first_name},</p>

                    <p class="text" style="font-size: 16px; color: #555;">
                        Welcome to the Supply Office! Your admin account has been successfully created. Here are your login credentials:
                    </p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 6px; margin: 20px 0; font-size: 16px;">
                        <p style="margin: 0;"><strong>Email:</strong> {email}</p>
                        <p style="margin: 0;"><strong>Password:</strong> {password}</p>
                    </div>

                    <p class="text" style="font-size: 16px; color: #555;">
                        For your security, please <strong style="color: #fdba74;">change your password</strong> after your first login.
                    </p>

                    <!-- Call-to-Action Button -->
                    
                    <p style="font-size: 14px; color: #777; margin-top: 30px;">
                        If you have any questions, reach out to our support team at 
                        <a href="mailto:manilajaylord_24@gmail.com" style="color: #fdba74; text-decoration: none;">support email</a>.
                    </p>
                </div>

                <!-- Footer Section -->
                <div class="footer" style="background-color: #f5f5f5; padding: 15px; text-align: center;">
                    <p style="font-size: 12px; color: #888; margin: 0;">
                        © 2024 Supply Office CTU-AC | Team SlapSoil
                    </p>
                    <p style="font-size: 12px; color: #888; margin: 5px 0 0;">
                        This is an automated message, please do not reply.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        if(ENVIRONMENT == "production"):
            send_mail_resend(email, subject, message)
        else:
            print(f'Email : {email}')
            print(f'Password : {password}')

        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")




def generate_password():
    # Generate a unique UUID and convert it to a string
    raw_uuid = uuid.uuid4()
    password = str(raw_uuid).replace("-", "")[:12]
    return password