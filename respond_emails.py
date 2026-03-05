import subprocess
import json
import base64
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
from google import genai

# 1. Environment configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GWS_CREDENTIALS = os.getenv("GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE")

# 2. Command line arguments handling
parser = argparse.ArgumentParser(description="AI Email Autoresponder")
parser.add_argument("--dry-run", action="store_true", help="Show responses without sending")
parser.add_argument("--limit-style", type=int, default=3, help="How many sent emails to fetch for style learning (default: 3)")
parser.add_argument("--limit-replies", type=int, default=1, help="How many new emails to reply to in one cycle (default: 1)")
parser.add_argument("--debug", action="store_true", help="Save detailed logs of incoming emails and generated replies to debug.log")
args = parser.parse_args()

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

def log_debug(message):
    """Logs debug information to debug.log file."""
    if args.debug:
        with open('debug.log', 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")

def run_gws(command_args):
    """Runs the gws CLI tool."""
    try:
        my_env = os.environ.copy()
        if GWS_CREDENTIALS:
            my_env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = GWS_CREDENTIALS

        result = subprocess.run(
            ['gws'] + command_args, 
            capture_output=True, 
            text=True, 
            check=True,
            env=my_env
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        err_output = e.stderr.strip() if e.stderr else e.stdout.strip()
        print(f"GWS Error: {err_output}")
        return None

def fetch_my_style_emails(limit):
    """Fetches sent email snippets for style learning."""
    print(f"🔍 Fetching {limit} messages for style learning...")
    list_response = run_gws([
        'gmail', 'users', 'messages', 'list',
        '--params', f'{{"userId": "me", "q": "in:sent", "maxResults": {limit}}}'
    ])
    
    if not list_response or 'messages' not in list_response:
        return []

    sent_texts = []
    for msg in list_response.get('messages', []):
        msg_data = run_gws(['gmail', 'users', 'messages', 'get', '--params', f'{{"userId": "me", "id": "{msg["id"]}"}}'])
        if msg_data and 'snippet' in msg_data:
            sent_texts.append(msg_data['snippet'])
    
    print(f"✅ Fetched {len(sent_texts)} style examples.")
    return sent_texts

def generate_reply(email_content, style_examples):
    """Generates a reply using Gemini 2.0 Flash."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    examples_str = "\n---\n".join(style_examples) if style_examples else "No examples."
    
    prompt = f"""
    You are my email assistant. Write a reply to the new message, mimicking my style:
    
    MY PREVIOUS MESSAGES (Style):
    {examples_str}
    
    RULES:
    1. If the question is about services, check information on dev.orpi.pl.
    2. The response should be short, specific, and in my style.
    
    NEW EMAIL CONTENT:
    {email_content}
    """
    
    try:
        response = client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def process_and_reply():
    """Main assistant loop."""
    if args.dry_run:
        print("\n🚀 [DRY-RUN MODE] Test mode active.\n")

    # Fetch styles with limit from flag
    style_examples = fetch_my_style_emails(args.limit_style)
    
    print(f"📩 Checking new messages (reply limit: {args.limit_replies})...")
    inbox_response = run_gws([
        'gmail', 'users', 'messages', 'list',
        '--params', f'{{"userId": "me", "q": "is:unread in:inbox", "maxResults": {args.limit_replies}}}'
    ])

    messages = inbox_response.get('messages', []) if inbox_response else []
    
    if not messages:
        print("😴 No new messages.")
        return

    for msg in messages:
        msg_id = msg['id']
        message_data = run_gws(['gmail', 'users', 'messages', 'get', '--params', f'{{"userId": "me", "id": "{msg_id}"}}'])
        
        if not message_data: continue

        headers = message_data.get('payload', {}).get('headers', [])
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Message")
        
        print(f"🤖 Analyzing email from: {sender}")
        
        email_snippet = message_data.get('snippet', '')
        log_debug(f"\n{'='*60}")
        log_debug(f"INCOMING EMAIL")
        log_debug(f"From: {sender}")
        log_debug(f"Subject: {subject}")
        log_debug(f"Content: {email_snippet}")
        log_debug(f"{'='*60}")
        
        reply_text = generate_reply(email_snippet, style_examples)
        
        if not reply_text: continue

        print(f"📝 Generated reply for {sender}:")
        print("-" * 30)
        print(reply_text)
        print("-" * 30)
        
        log_debug(f"\nGENERATED REPLY")
        log_debug(f"To: {sender}")
        log_debug(f"Reply: {reply_text}")
        log_debug(f"{'='*60}\n")

        if args.dry_run:
            print(f"⏩ [DRY-RUN] Skipped sending to {sender}.\n")
            continue

        # Prepare and send
        reply_email = EmailMessage()
        reply_email.set_content(reply_text)
        reply_email['To'] = sender
        reply_email['Subject'] = subject if subject.startswith("Re:") else f"Re: {subject}"
        raw_msg = base64.urlsafe_b64encode(reply_email.as_bytes()).decode('utf-8')

        send_result = run_gws([
            'gmail', 'users', 'messages', 'send',
            '--params', '{"userId": "me"}',
            '--json', json.dumps({'raw': raw_msg, 'threadId': message_data['threadId']})
        ])

        if not send_result:
            print(f"❌ Failed to send reply to {sender}. Skipping.\n")
            log_debug(f"ERROR: Failed to send email to {sender}")
            continue

        modify_result = run_gws([
            'gmail', 'users', 'messages', 'modify',
            '--params', f'{{"userId": "me", "id": "{msg_id}"}}',
            '--json', '{"removeLabelIds": ["UNREAD"]}'
        ])
        
        if modify_result:
            print(f"✅ Reply sent to {sender}.\n")
            log_debug(f"SUCCESS: Email sent and marked as read for {sender}")
        else:
            print(f"⚠️  Reply sent to {sender}, but failed to mark as read.\n")
            log_debug(f"WARNING: Email sent to {sender} but failed to mark as read")

if __name__ == '__main__':
    process_and_reply()