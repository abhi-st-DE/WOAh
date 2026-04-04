import os
import time
import json
import base64
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from gmail_auth import get_gmail_service
from pydantic import BaseModel, Field
from huggingface_hub import InferenceClient


# inference from hugging face validation.
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN") 
if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not accessible from environment variables.")
client = InferenceClient(
    api_key=HF_TOKEN,
    model="moonshotai/Kimi-K2-Thinking"
)


def get_email_body(payload):
    """Recursively searches the Gmail payload, decodes Base64, and parses HTML into plain text."""
    plain_text_body = ""
    html_text_body = ""
    
    # 1. Check if the payload itself is the raw data 
    if 'data' in payload.get('body', {}):
        data = payload['body']['data']
        if len(data) % 4: data += '=' * (4 - len(data) % 4)
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
                if len(data) % 4: data += '=' * (4 - len(data) % 4)
                plain_text_body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore') + "\n"
            
            # Catch HTML and strip the tags using BeautifulSoup
            elif mime_type == 'text/html':
                data = part['body'].get('data', '')
                if len(data) % 4: data += '=' * (4 - len(data) % 4)
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

        
def sweep_inbox(iterations=1, wait_time=15):
    """
    Performs a controlled sweep of the inbox for a specific number of iterations.
    Perfect for an AI to call without getting trapped in an infinite loop.
    """
    print(f"\n🚀 Starting Mail Sweep: {iterations} iterations, waiting {wait_time}s between checks.")
    
    service = get_gmail_service()
    archive_file = "email_archive.txt"
    seen_emails = set()
    total_saved_this_session = 0
    
    # ---------------------------------------------------------
    # TASK 2: Check local file and load memory
    # ---------------------------------------------------------
    if os.path.exists(archive_file):
        with open(archive_file, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("ID:       "):
                    extracted_id = line.replace("ID:       ", "").strip()
                    seen_emails.add(extracted_id)
        print(f"🧠 Memory loaded. Found {len(seen_emails)} old emails.")
    else:
        print("🧠 First run: No archive found. Creating new memory.")

    categories = [
        {"name": "Inbox",     "params": {"labelIds": ['INBOX']}},
        {"name": "Sent",      "params": {"labelIds": ['SENT']}},
        {"name": "Unread",    "params": {"labelIds": ['UNREAD']}},
        {"name": "Starred",   "params": {"labelIds": ['STARRED']}},
        {"name": "Important", "params": {"labelIds": ['IMPORTANT']}}
    ]
    
    # ---------------------------------------------------------
    # TASK 3 & TASK 1: Loop for a predefined number of times and fetch
    # ---------------------------------------------------------
    for current_loop in range(iterations):
        print(f"\n--- Sweep {current_loop + 1} of {iterations} ---")
        
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
                        
                        print(f"🚨 NEW [{category['name'].upper()}] CAUGHT: {sender}")
                        append_full_email_to_system_file(full_email, category['name'], msg_id, archive_file)
                        total_saved_this_session += 1
            
            # If we are not on the last iteration, wait 15 seconds
            if current_loop < iterations - 1:
                print(f"Waiting {wait_time} seconds before next sweep...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"⚠️ Error checking emails: {e}")
            break # Exit the loop safely if Google's API crashes

    # ---------------------------------------------------------
    # TASK 4: System Shutdown / Return Status
    # ---------------------------------------------------------
    print("\n🛑 Sweep Complete. Shutting down process safely.")
    
    # Returning a string is crucial for the AI. It tells the AI the job is done!
    return f"Success: Completed {iterations} sweeps. Saved {total_saved_this_session} new emails to the archive."


class SweepInboxArgs(BaseModel):
    iterations: int = Field(
        default=1,
        description="How many times to check for new emails. Default is 1."
    )
    wait_time: int = Field(
        default=15,
        description="Seconds to wait between checks if iterations is greater than 1. Default is 15."
    )

schema_sweep_inbox = {
    "type": "function",
    "function": {
        "name": "sweep_inbox",
        "description": "Scans the user's Gmail (Inbox, Sent, Unread, etc.) for new emails, saves them to a local text file archive, and returns a summary of how many new emails were saved.",
        "parameters": SweepInboxArgs.model_json_schema()    
    }
}

class Agent:
    def __init__(self, client: InferenceClient, system: str = "", tools: list = None) -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        self.tools = tools if tools is not None else []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})

        final_assistant_content = self.execute()

        if final_assistant_content:
            self.messages.append({"role": "assistant", "content": final_assistant_content})

        return final_assistant_content
    def execute(self):
        while True:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto" # Let the model decide when to call tools.
            )

            response_message = completion.choices[0].message

            if response_message.tool_calls:
                self.messages.append(response_message)
            # tools responses comes only after tool call, 
            # and if your agent don't has in his history it tool calls, it won't be able to respond.

                tool_outputs =[]
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    tool_output_content = f"Error: Tool '{function_name}' not found."

                    # Execute the tool
                    if function_name in globals() and callable(globals()[function_name]):
                        function_to_call = globals()[function_name]
                        executed_output = function_to_call(**function_args)
                        tool_output_content = str(executed_output) # Ensure output is a string.
                        print(f"Executing tool: {function_name} with args {function_args}, Output: {tool_output_content[:500]}...") # Debug print

                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_output_content,
                        }
                    )
                self.messages.extend(tool_outputs)
            else:
                return response_message.content

# Initialisation
system =  (
    " You are a helpful assistant that is capable of retrieving information about the mails and provide it back. "
    " When the user give you a number of seconds to wait you calculate the wait time and wait patiently. "
)

tools = [schema_sweep_inbox]

agent = Agent(client, system, tools)

response = agent("save my recent mails to the file, and also wait for the next 30 seconds a new mail is also coming.")

print(f"final answer: {response}")

mess = agent.messages

print(f"agent messages are:", mess)

