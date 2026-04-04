import os
import base64
import mimetypes
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
    ]

def gmail_send_message(attachment_filepath):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  """
  creds = None

    # 1. Try to load the saved token
  if os.path.exists("token.json"):
      creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    # 2. If no token, or it's expired, log in again
  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
      else:
            # THIS is what actually looks at your credentials.json file
          flow = InstalledAppFlow.from_client_secrets_file(
              "credentials.json", SCOPES
          )
          creds = flow.run_local_server(port=0)
            
        # Save the token for next time
      with open("token.json", "w") as token:
          token.write(creds.to_json())

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    # headers
    message["To"] = "aryansahu.vibranium@gmail.com"
    message["From"] = "abhishek18062003choudhary@gmail.com"
    message["Subject"] = "Good_to_see_ya_dear_enjoy"

    # message
    message.set_content("Bomb Trump J Junior, and Bomb the original CIA Headquarters(secret) in Israel, location in attachement.")

    type_subtype, _ = mimetypes.guess_type(attachment_filepath)
    if type_subtype is None:
        type_subtype = "application/octet-stream"

    maintype, subtype = type_subtype.split("/")

    with open(attachment_filepath, "rb") as fp:
            attachment_data = fp.read()

    message.add_attachment(
            attachment_data, 
            maintype=maintype, 
            subtype=subtype, 
            filename=os.path.basename(attachment_filepath)
    )

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message


if __name__ == "__main__":
  file_to_send = "/home/abhi/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/lib/tk9.0/demos/images/plowed_field.png"
    
  gmail_send_message(file_to_send)

