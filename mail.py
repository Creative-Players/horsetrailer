import os
import pickle
import base64
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def service_gmail():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def decode_message_part(data):
    """Decode email body data."""
    byte_code = base64.urlsafe_b64decode(data.encode('UTF-8'))
    return byte_code.decode('utf-8')

def list_emails_to_excel(filename='emails.xlsx'):
    service = service_gmail()
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    email_data = []

    if not messages:
        print("No messages found.")
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            msg_data = {'sender': '', 'subject': '', 'snippet': '', 'body': ''}
            headers = msg.get('payload', {}).get('headers', [])
            for header in headers:
                if header['name'].lower() == 'from':
                    msg_data['sender'] = header['value']
                if header['name'].lower() == 'subject':
                    msg_data['subject'] = header['value']

            msg_data['snippet'] = msg.get('snippet', '')

            # Getting the body of the email
            part = msg['payload']
            if part['mimeType'] == 'text/plain':
                msg_data['body'] = decode_message_part(part['body']['data'])
            elif part['mimeType'] == 'multipart/alternative':
                for sub_part in part['parts']:
                    if sub_part['mimeType'] == 'text/plain':
                        msg_data['body'] = decode_message_part(sub_part['body']['data'])

            email_data.append(msg_data)

    # Create a pandas DataFrame
    df = pd.DataFrame(email_data)

    # Export the DataFrame to an Excel file
    df.to_excel(filename, index=False)

    print(f"Exported {len(df)} emails to {filename}")

if __name__ == '__main__':
    list_emails_to_excel()
