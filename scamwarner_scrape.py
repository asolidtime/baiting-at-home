from bs4 import BeautifulSoup
import re
import requests
import json

def extract_emails(text):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_regex, text)

def download_page(url, session_id):
    session = requests.Session()
    # note: requires flaresolverr running on localhost:8191
    # docker run -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
    response = session.post('http://localhost:8191/v1', json={
        'cmd': 'request.get',
        'url': url,
        'session': session_id,
        'maxTimeout': 600000
    })
    print(response.json())
    response_data = response.json()
    soup = BeautifulSoup(response_data['solution']['response'], 'html.parser')
    return soup

def create_session():
    session = requests.Session()
    response = session.post('http://localhost:8191/v1', json={
        'cmd': 'sessions.create',
    })
    print(response.json())
    response_data = response.json()
    return response_data['session']

session_id = create_session()

def extract_emails_from_soup(soup):
    text = soup.get_text()
    print(text)
    return extract_emails(text)

def download_and_extract(url, session_id):
    soup = download_page(url, session_id)
    return extract_emails_from_soup(soup)

def destroy_session(session_id):
    session = requests.Session()
    response = session.post('http://localhost:8191/v1', json={
        'cmd': 'sessions.destroy',
        'session': session_id,
    })
    print(response.json())

forum_ids = [43, 36, 6, 39, 12, 13, 35, 34, 42, 14, 8, 40, 9]
# forum_ids = [6, 39, 12, 13, 35, 34, 42, 14, 8, 40, 9]
# forum_ids = [7]
with open('emails.txt', 'a') as f:
    for forum_id in forum_ids:
        start = 0
        while start < 200:
            try:
                url = f"https://www.scamwarners.com/forum/viewforum.php?f={forum_id}&start={start}"
                emails = download_and_extract(url, session_id)
                for email in emails:
                    print(email)
                    f.write(email + '\n')
                start += 50
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 404:
                    break
                else:
                    raise
            except KeyError as err:
                print(err)
                destroy_session(session_id)
                session_id = create_session()
destroy_session(session_id)
