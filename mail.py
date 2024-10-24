import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, attachment_path):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the body to the message
    msg.attach(MIMEText(body, 'plain'))

    # Open the file to be sent
    filename = os.path.basename(attachment_path)
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    # Encode the file in base64
    encoders.encode_base64(part)

    # Add the header to the attachment
    part.add_header('Content-Disposition', f'attachment; filename={filename}')

    # Attach the file to the message
    msg.attach(part)

    # Set up the SMTP server and login
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Start TLS encryption
    server.login(sender_email, sender_password)

    # Send the email
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)

    # Quit the server
    server.quit()

    print(f'Email sent to {receiver_email} with attachment {filename}')

# Example usage
sender_email = 'jhanvipandya325@gmail.com'
sender_password = 'hklx fvpj amrw pokp'
receiver_email = 'jhanvipandya325@gmail.com'
subject = 'Subject: File with flagged reward functions'
body = 'Please find the attached file.'
attachment_path = 'file.txt'

send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, attachment_path)
