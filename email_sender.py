import smtplib
import random
from email.message import EmailMessage
import os


def send_mail(email, otp):
    sender_email = ""
    receiver_email = email
    message = EmailMessage()
    message["Subject"] = "inline embedding"
    message["From"] = sender_email
    message["To"] = receiver_email

    # encoded = base64.b64encode(open("mailtrap.jpg", "rb").read()).decode()
    email_to_send = '''
        <!DOCTYPE html>
        <html>
            <head>
                <link
                    rel="stylesheet"
                    type="text/css"
                    hs-webfonts="true"
                    href="https://fonts.googleapis.com/css?family=Lato|Lato:i,b,bi"
                />
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <style type="text/css">
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #00aaff;
                    }

                    img {
                        width: -webkit-fill-available;
                    }

                    .container {
                        width: fit-content;
                        margin: 50px auto;
                        background-color: #fff;
                        box-shadow: 0 2px 4px rgba(0, 0, 0);
                        text-align: center;
                    }

                    .sub-container {
                        padding: 20px;
                    }

                    .logo {
                        padding: 19px;
                        max-width: 60px;
                        margin: 0 auto;
                        background: linear-gradient(180deg, #ffeb3b, transparent);
                        border-radius: 50%;
                    }

                    .otp {
                        font-size: 2rem;
                        font-weight: 500;
                        color: #000000;
                        margin: 30px auto;
                        letter-spacing: 4px;
                        background: #f2f2f2;
                        max-width: fit-content;
                        padding: 10px;
                        border-radius: 7px;
                    }

                    .otp span {
                        display: block;
                        margin-bottom: 10px;
                    }

                    .otp-expires {
                        font-size: 0.8rem;
                        color: #ff5050;
                        margin-bottom: 0;
                    }

                    .links {
                        margin-bottom: 30px;
                    }

                    .links a {
                        display: inline-block;
                        margin: 0 5px;
                        color: #4a86e8;
                        text-decoration: none;
                        font-size: 0.8rem;
                        padding: 5px;
                        border-radius: 3px;
                        border: 1px solid #4a86e8;
                    }

                    .links a:hover {
                        background-color: #4a86e8;
                        color: #fff;
                    }
                </style>
            </head>
            <body>
                <html>
                    <body>
                        <div class="container">
                            <p style="font-weight: bold; background-color: #4a86e8; color: white; padding: 30px; font-size: 25px;">SPENDWISE</p>
                            <div class="sub-container">
                                <p>
                                    Here is your One Time Password to validate your
                                    email address<br />
                                </p>
                                <div class="otp">''' + str(otp) + '''</div>
                                <p class="otp-expires">Valid for 10 minutes only</p>
                                <p>
                                    <a href="FAQs">FAQs</a> |
                                    <a href="Terms & Conditions">Terms & Conditions</a>
                                    |
                                    <a href="Contact Us">Contact Us</a>
                                </p>
                            </div>
                        </div>
                    </body>
                </html>
            </body>
        </html>

        '''
    message.set_content(email_to_send, subtype='html')

    with smtplib.SMTP(host='smtp.gmail.com', port=587, timeout=120) as connection:
        connection.starttls()
        connection.login(user=sender_email, password="")
        connection.sendmail(sender_email,
                            receiver_email,
                            msg=message.as_string())
