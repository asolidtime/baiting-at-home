import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
from time import sleep
import random

def send_mail(to_addresses, username, password, smtp_url, smtp_port, name):
    # Create a multipart message
    msg = MIMEMultipart()

    # Setup the parameters of the message
    msg['From'] = username
    msg['To'] = to_addresses[0]  # The first email address in the list
    msg['Bcc'] = ', '.join(to_addresses[1:])  # The rest of the email addresses in the list
    msg['Subject'] = "Continuing our conversation"

    # Add the message body
    msg.attach(MIMEText(f"Hey there,\n\nI think you started a conversation with me on my old email. I'm continuing it here, since I don't use the old one anymore.\n\nThanks,\n{name}", 'plain'))

    # Setup the SMTP server
    server = smtplib.SMTP(smtp_url, smtp_port)
    server.starttls()

    # Login to the SMTP server
    server.login(username, password)

    # Send the email
    server.send_message(msg)

    # Terminate the SMTP session
    server.quit()

def main():
    logins_file_path = os.path.expanduser('~/.config/bah/logins.json')
    with open(os.path.expanduser(logins_file_path), 'r') as file:
        logins = json.load(file)

    with open('newemails-copy.txt', 'r') as file:
        emails = [line.strip() for line in file if line.strip()]

    total_emails = len(emails)  # Total number of emails

    for i in range(0, total_emails, 10):  # Start counting from 0, increment by 30
        email_batch = emails[i:i+10]
        for login in logins:
            if login['email_username'].endswith("superturbojeremy@gmail.com"):
            # if True:
                email_username = login['email_username']
                email_password = login['email_password']
                email_smtp_url = login['email_smtp_url']
                email_smtp_port = login['email_smtp_port']
                name = login['name']

                print(f"Sending email batch starting with {i+1} of {total_emails} ({(i+1)/total_emails*100:.2f}%) from {email_username}")
                try:
                    send_mail(email_batch, email_username, email_password, email_smtp_url, email_smtp_port, name)
                except smtplib.SMTPDataError as err:
                    print(err)
                    exit(1)
        sleep(1800)
        

if __name__ == "__main__":
    main()
