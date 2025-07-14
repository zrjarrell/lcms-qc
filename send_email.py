import smtplib, json
from email.mime.text import MIMEText

# https://mailtrap.io/blog/python-send-email-gmail/#Send-email-in-Python-using-Gmail-SMTP

config = json.load(open("email_config.json"))

def send_email(subject, body, sender = config["sender"], recipients = config["recipients"], password = config["password"]):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")