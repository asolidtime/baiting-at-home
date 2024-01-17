from collections import Counter

with open('emails-all-small.txt', 'r') as f:
    emails = f.read().splitlines()

email_counts = Counter(emails)

# Create a new list to hold the emails after deletion
new_emails = []

for email, count in email_counts.items():
    new_emails.append(email)

# Write the new list back to the file
with open('newemails.txt', 'w') as f:
    for email in new_emails:
        f.write(email + '\n')
