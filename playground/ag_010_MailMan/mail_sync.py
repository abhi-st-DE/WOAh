import time
import base64
import os
from bs4 import BeautifulSoup
from gmail_auth import get_gmail_service

def get_email_body(payload):
    """Recursively searches the Gmail payload, decodes Base64, and parses HTML into plain text."""
    plain_text_body = ""
    html_text_body = ""
    
    # 1. Check if the payload itself is the raw data 
    if 'data' in payload.get('body', {}):
        data = payload['body']['data']
        data += '=' * (4 - len(data) % 4) 
        raw_decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # If the main payload is HTML, clean it
        if payload.get('mimeType') == 'text/html':
            return BeautifulSoup(raw_decoded, "html.parser").get_text(separator='\n', strip=True)
        return raw_decoded
    
    # 2. Iterate through parts if it's a multipart email
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType')
            
            # Catch Plain Text
            if mime_type == 'text/plain':
                data = part['body'].get('data', '')
                data += '=' * (4 - len(data) % 4)
                plain_text_body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore') + "\n"
            
            # Catch HTML and strip the tags using BeautifulSoup
            elif mime_type == 'text/html':
                data = part['body'].get('data', '')
                data += '=' * (4 - len(data) % 4)
                raw_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
                # get_text() removes all HTML tags and leaves only the visible words
                clean_html_text = BeautifulSoup(raw_html, "html.parser").get_text(separator='\n', strip=True)
                html_text_body += clean_html_text + "\n"
            
            # Dive deeper if there are nested parts (Fixing the recursion bug)
            elif 'parts' in part:
                nested_result = get_email_body(part)
                if nested_result != "No readable text found.":
                    plain_text_body += nested_result + "\n"
                
    # 3. Decide what to return
    # We prefer the originally intended plain text, but fall back to the cleaned HTML if plain text doesn't exist.
    if plain_text_body.strip():
        return plain_text_body.strip()
    elif html_text_body.strip():
        return html_text_body.strip()
    else:
        return "No readable text found."

def append_full_email_to_system_file(doc, category_name, msg_id, filename="email_archive.txt"):
    """Saves the email AND the ID so the file acts as its own memory."""
    try:
        headers = doc['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        date = next((h['value'] for h in headers if h['name'] == 'Date'), "Unknown Date")
        
        body_content = get_email_body(doc['payload'])

        with open(filename, "a", encoding="utf-8") as file:
            file.write("="*80 + "\n")
            file.write(f"ID:       {msg_id}\n") # <--- NEW: Saves the ID
            file.write(f"CATEGORY: {category_name.upper()}\n") 
            file.write(f"DATE:     {date}\n")
            file.write(f"FROM:     {sender}\n")
            file.write(f"SUBJECT:  {subject}\n")
            file.write("-" * 80 + "\n")
            file.write(f"{body_content}\n\n")
            
    except Exception as e:
        print(f"❌ Failed to append full email to file: {e}")

def run_radar(check_interval=15):
    print("\n📡 Multi-Tag Email Radar Turned ON.")
    print("Press Ctrl+C to stop the radar.\n" + "-"*40)
    
    service = get_gmail_service()
    
    # ---------------------------------------------------------
    # NEW: SELF-CONTAINED MEMORY SYSTEM
    # ---------------------------------------------------------
    archive_file = "email_archive.txt"
    seen_emails = set()
    
    # Wake up and read the ARCHIVE file directly
    if os.path.exists(archive_file):
        with open(archive_file, "r", encoding="utf-8") as file:
            for line in file:
                # Hunt for the specific ID line we created
                if line.startswith("ID:       "):
                    # Strip away the "ID:       " part and the invisible newline character
                    extracted_id = line.replace("ID:       ", "").strip()
                    seen_emails.add(extracted_id)
                    
        print(f"🧠 Memory restored from archive! Remembering {len(seen_emails)} old emails.")
    else:
        print("🧠 First run: No archive found. Memory is blank.")
    # ---------------------------------------------------------

    categories = [
        {"name": "Inbox",     "params": {"labelIds": ['INBOX']}},
        {"name": "Sent",      "params": {"labelIds": ['SENT']}},
        {"name": "Unread",    "params": {"labelIds": ['UNREAD']}},
        {"name": "Read",      "params": {"q": 'is:read'}}, 
        {"name": "Starred",   "params": {"labelIds": ['STARRED']}},
        {"name": "Important", "params": {"labelIds": ['IMPORTANT']}}
    ]
    
    while True:
        try:
            for category in categories:
                results = service.users().messages().list(userId='me', maxResults=5, **category["params"]).execute()
                messages = results.get('messages', [])
                
                for msg in messages:
                    msg_id = msg['id']
                    
                    if msg_id not in seen_emails:
                        seen_emails.add(msg_id) 
                        
                        full_email = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                        
                        sender = next((h['value'] for h in full_email['payload']['headers'] if h['name'] == 'From'), "Unknown")
                        print(f"\n🚨 NEW [{category['name'].upper()}] CAUGHT: {sender}")
                        
                        # Pass the msg_id to the save function!
                        append_full_email_to_system_file(full_email, category['name'], msg_id, archive_file)
                        print(f"📝 Saved to archive.")
            
            print(".", end="", flush=True)
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"\n⚠️ Error checking emails: {e}")
            time.sleep(check_interval)

if __name__ == '__main__':
    try:
        run_radar()
    except KeyboardInterrupt:
        print("\n\n🛑 Radar Turned OFF (You pressed Ctrl+C).")