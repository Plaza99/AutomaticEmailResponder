from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import time, sys, os.path
from utils import utils


creds = None
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify",
          "https://www.googleapis.com/auth/gmail.compose"]


def main():

    # Print banner
    with open("utils/banner.txt", "r") as banner_file:
        banner = banner_file.read()
        print(banner)

    # Create utils folder if not exists
    if not os.path.exists("utils"):
        os.makedirs("utils")

    # Retrieve args from command line (sleep_time)
    sleep_time = 10
    if len(sys.argv) > 1:
        if isinstance(int(sys.argv[1]), int):
            sleep_time = int(sys.argv[1])
            print("Sleep time (seconds) set to: ", sleep_time)
        else:
            return print("ERROR: invalid argument! Time argument must be an integer.")
    else:
        print("No sleep time (seconds) specified, default value set to: ", sleep_time)

    # Retrieve promp for ChatGPT
    if os.path.exists("utils/prompt.txt") and os.path.getsize("utils/prompt.txt") > 0:
        with open("utils/prompt.txt", "r") as prompt_file:
            prompt = prompt_file.read()
            print("Prompt retrieved, summary: '" + prompt[0:50] + (prompt[50:] and '..') + "'")
    else:
        with open("utils/prompt.txt", "w") as prompt_file:
            prompt_file.write("Insert your prompt here")
        return print("ERROR: prompt file not found or empty! File created inside utils folder. Please insert your prompt and restart the app.")
    
    # Authenticate with Google API
    authenticate()
    print("Gmail authentication completed")

    # Check opeanAI key
    if(os.path.exists(os.path.join(os.getcwd(), "utils/openai-key.txt"))):
        with open(os.path.join(os.getcwd(), "utils/openai-key.txt"), "r") as key_file:
            os.environ['OPENAI_API_KEY'] = key_file.read()
            print("OpenAI key retrieved")
    else:
        return print("ERROR: OpenAI key file not found! Please insert your key inside utils folder and restart the app.")

    # Confirm config
    print("Are you sure you want to start the app with these settings? (y/n)\n")
    confirm = input()
    if confirm.lower() != "y":
        return print("App closed.")

    # Main loop
    print("--------------------------------------------------")
    print("App started\n")
    while(1):
        try:
            service = build("gmail", "v1", credentials=creds)
            results = service.users().messages().list(userId="me", q="{is:unread AND label:inbox}").execute()
            message_list = results.get("messages", [])

            if not message_list:
                print("No new incoming messages found.")
            else:    
                print("Incoming messages:\n")
                for message in message_list:
                    result = service.users().messages().get(userId="me",id=message["id"]).execute()
                    msg = utils.create_msg_obj(result)
                    reply = utils.generate_response(msg['snippet'], prompt)
                    utils.mark_as_readed(msg['id'], creds)
                    utils.create_response(msg, reply, creds)
                    print("\n\n\n")
        except HttpError as error:
            print(f"An error occurred: {error}")

        time.sleep(sleep_time) # delay in seconds





# Authenticate with Google API function
def authenticate():
    global creds
    if os.path.exists("utils/token.json"):
        creds = Credentials.from_authorized_user_file("utils/token.json", SCOPES)
          
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("utils/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("utils/token.json", "w") as token:
            token.write(creds.to_json())


# Run main function
if __name__ == "__main__":
    main()
