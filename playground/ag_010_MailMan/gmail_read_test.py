# read_full_email.py
import base64
from gmail_auth import get_gmail_service

def extract_text_body(payload):
    """Digs through the email "boxes" to find and unscramble the plain text."""
    
    # 1. If the email has multiple boxes (Text + HTML + Attachments)
    if 'parts' in payload:
        for part in payload['parts']:
            # We found the pure text box!
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                # The '===' is a safety trick to prevent Python padding errors
                return base64.urlsafe_b64decode(data + "===").decode('utf-8')
            
            # If there are boxes inside of boxes (nested parts), dig deeper
            elif 'parts' in part:
                found_text = extract_text_body(part)
                if found_text:
                    return found_text

    # 2. If it's a super simple email with no nested boxes
    else:
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data + "===").decode('utf-8')
            
    return "No plain text found in this email."


def read_latest_full_email():
    try:
        # Grab your Master Key
        service = get_gmail_service()
        
        print("Fetching your latest email...\n" + "-"*40)
        
        # Get just the newest 1 email ID
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            print("Your inbox is empty.")
            return

        msg_id = messages[0]['id']
        
        # IMPORTANT: We changed 'metadata' to 'full'
        full_email = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        # Extract the Headers (Subject and From)
        headers = full_email['payload']['headers']
        subject = "No Subject"
        sender = "Unknown Sender"
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']
                
        # Use our new function to dig out the message text
        body_text = extract_text_body(full_email['payload'])

        # Print the final result
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print("\n--- FULL MESSAGE ---")
        print(body_text)
        print("-" * 40)

    except Exception as error:
        print(f"An error occurred: {error}")

if __name__ == '__main__':
    read_latest_full_email()