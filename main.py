import time
import imaplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import parseaddr
import requests
import json
from icecream import ic
import re
import base64
import os

# Define the file paths
logins_file_path = os.path.expanduser('~/.config/bah/logins.json')
context_file_path = os.path.expanduser('~/.local/bah/context.json')

# Check if the logins file exists and create it if it doesn't
if not os.path.exists(logins_file_path):
    os.makedirs(os.path.dirname(logins_file_path), exist_ok=True)
    with open(logins_file_path, 'w') as file:
        file.write("""
[
    {
        "name": "Example Name",
        "system_prompt": "Your name is Example Name. The queries you receive are scam emails. Do not reveal that you know this. Do not say that you are an AI language model. Respond in a way that wastes the scammers' time as much as possible.",
        "email_username": "examplemail1234@gmail.com",
        "email_password": "ExamplePassword",
        "email_imap_url": "imap.gmail.com",
        "email_smtp_url": "smtp.gmail.com",
        "email_smtp_port": 587
    }
]""")

# Check if the config file exists and create it if it doesn't
if not os.path.exists(context_file_path):
    os.makedirs(os.path.dirname(context_file_path), exist_ok=True)


ic.configureOutput(prefix='{time} | ')
ic.enable()


context_dict = {}



try:
    # Try to open the file and load the JSON
    with open(os.path.expanduser(context_file_path), 'r') as file:
        context_dict = json.load(file)
except FileNotFoundError:
    # If the file doesn't exist, set context_dict to an empty dictionary
    context_dict = {}

def get_response(email_content, sender_email, system_prompt, name):
    url = "http://192.168.1.155:11434/api/generate"  # Ollama server URL
    
    context_dict.setdefault(sender_email, [])
    
    context_dict[sender_email].append(f"[INST]{sender_email}:\n\n{email_content}[/INST]")

    actual_prompt = f"<<SYS>>{system_prompt}<</SYS>><s>" + '\n'.join(context_dict[sender_email][-3:]) + f"\n{name}:"

    data = {
        "model": "jasonscb-noctx-creative",  # Use the model you want
        "prompt": actual_prompt,  # Use the email content as the prompt
        "stream": False,  # Use the non-streaming API
        "raw": True
    }
    headers = {'Content-Type': 'application/json'}
    ic(json.dumps(data))
    response = requests.post(url, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        context_dict[sender_email].append(response.json()['response'])
        return response.json()['response']

    else:
        print(f"Error: {response.status_code}")
        return None

def extract_emails(email_content):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email_content)

def check_mail(username, password, imap_url, name):
    # Connect to the server
    mail = imaplib.IMAP4_SSL(imap_url)

   # Login to your account
    mail.login(username, password)

    # Select the mailbox you want to check
    mail.select("inbox")

    # Search for unseen emails
    result, data = mail.uid('search', None, "UNSEEN")
    email_ids = data[0].split()

    # If there are no new emails, return None
    if not email_ids:
        return None, None, None, None

    # Get the most recent email id
    latest_email_id = email_ids[-1]

    # Fetch the full email (headers + body)
    result, data = mail.uid('fetch', latest_email_id, "(BODY[])")

    # Parse the raw email
    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)

    # Decode and parse the "From" header to extract the sender's email address
    from_header = decode_header(email_message['From'])[0]
    if isinstance(from_header[0], bytes):
        sender_email = parseaddr(from_header[0].decode(from_header[1] if from_header[1] else 'utf8'))[1]
    else:
        sender_email = parseaddr(from_header[0])[1]
        
    email_content = ""

    if email_message.is_multipart():
        for part in email_message.walk():
            ic(part.get_content_type())
            if part.get_content_type().startswith("text/pl"):
                ic(part.get_content_type())
                payload = part.get_payload()
                try:
                    # Try to decode the payload from Base64
                    decoded_payload = base64.b64decode(payload).decode('utf-8')
                    email_content += decoded_payload
                except (base64.binascii.Error, UnicodeDecodeError):
                    # If decoding fails, use the original payload
                    email_content += payload
    else:
        print("email message is not multipart")
        email_content = email_message.get_payload()
        
    email_content = email_content.split(f"{name} <{username}> wrote:")[0]
    email_content = email_content.split(f"{name} <{username}>:")[0]
    email_content = email_content.split(f"<{username}> wrote:")[0]
    email_content = email_content.split(f"<{username}>:")[0]
    # Mark the email as seen
    mail.uid('store', latest_email_id, '+FLAGS', '\\Seen')

    # Get the original message's Message-ID and Subject
    original_message_id = email_message['Message-ID']
    original_subject = decode_header(email_message['Subject'])[0][0]

    # Return the email content and sender's email address
    return email_content, sender_email, original_message_id, original_subject



def send_mail(response, to_address, original_message_id, original_subject, linked_emails, username, password, smtp_url, smtp_port):
    # Create a multipart message
    msg = MIMEMultipart()

    # Setup the parameters of the message
    msg['From'] = username
    all_recipients = [to_address] + linked_emails
    msg['To'] = ', '.join(all_recipients)
    try:
        msg['Subject'] = "Re: " + original_subject
    except TypeError:
        msg['Subject'] = "Re: " + original_subject.decode('utf-8')
    msg['In-Reply-To'] = original_message_id
    msg['References'] = original_message_id

    # Add the message body
    msg.attach(MIMEText(response, 'plain'))

    # Setup the SMTP server
    server = smtplib.SMTP(smtp_url, smtp_port)
    server.starttls()

    # Login to the SMTP server
    server.login(username, password)

    # Send the email
    server.send_message(msg)

    # Terminate the SMTP session
    server.quit()


import json

if __name__ == "__main__":
    with open(os.path.expanduser(logins_file_path), 'r') as file:
        logins = json.load(file)
        if logins[0]['email_username'] == "examplemail1234@gmail.com":
            print(f"Error: no email configured\nFill out the config file at {logins_file_path} to include your email login")
            exit(1)

    for login in logins:
        system_prompt = login['system_prompt']
        email_username = login['email_username']
        email_password = login['email_password']
        email_imap_url = login['email_imap_url']
        email_smtp_url = login['email_smtp_url']
        email_smtp_port = login['email_smtp_port']
        name = login['name']

        email_content, sender_email, original_message_id, original_subject = check_mail(email_username, email_password, email_imap_url, name)

        if email_content and sender_email and sender_email != email_username:
            print(f"email_content: {email_content}\n"
              f"sender_email: {sender_email}\n"
              f"original_message_id: {original_message_id}\n"
              f"original_subject: {original_subject}\n")
            response = get_response(email_content, sender_email, system_prompt, name)
            linked_emails = extract_emails(email_content)
            ic(response)
            ic(linked_emails)

            send_mail(response, sender_email, original_message_id, original_subject, linked_emails, email_username, email_password, email_smtp_url, email_smtp_port)
        else:
            ic("inbox empty")
            
with open(os.path.expanduser(context_file_path), 'w') as file:
    # Write the dictionary to the file as JSON
    json.dump(context_dict, file)
