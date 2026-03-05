import subprocess
import json
import base64
import os
import argparse
from dotenv import load_dotenv
from email.message import EmailMessage
from google import genai

# 1. Konfiguracja środowiska
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GWS_CREDENTIALS = os.getenv("GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE")

# 2. Obsługa argumentów linii komend
parser = argparse.ArgumentParser(description="AI Email Autoresponder")
parser.add_argument("--dry-run", action="store_true", help="Pokaż odpowiedzi bez wysyłania")
parser.add_argument("--limit-style", type=int, default=3, help="Ile wysłanych maili pobrać do nauki stylu (domyślnie: 3)")
parser.add_argument("--limit-replies", type=int, default=1, help="Na ile nowych maili odpowiedzieć w jednym cyklu (domyślnie: 1)")
args = parser.parse_args()

if not GEMINI_API_KEY:
    print("BŁĄD: Nie znaleziono GEMINI_API_KEY w pliku .env")
    exit(1)

def run_gws(command_args):
    """Uruchamia narzędzie gws CLI."""
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
        print(f"Błąd GWS: {err_output}")
        return None

def fetch_my_style_emails(limit):
    """Pobiera skróty wysłanych maili do nauki stylu."""
    print(f"🔍 Pobieram {limit} wiadomości do nauki stylu...")
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
    
    print(f"✅ Pobrano {len(sent_texts)} przykładów stylu.")
    return sent_texts

def generate_reply(email_content, style_examples):
    """Generuje odpowiedź za pomocą Gemini 2.0 Flash."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    examples_str = "\n---\n".join(style_examples) if style_examples else "Brak przykładów."
    
    prompt = f"""
    Jesteś moim asystentem e-mailowym. Napisz odpowiedź na nową wiadomość, naśladując mój styl:
    
    MOJE POPRZEDNIE WIADOMOŚCI (Styl):
    {examples_str}
    
    ZASADY:
    1. Jeśli pytanie dotyczy usług, sprawdź informacje na stronie dev.orpi.pl.
    2. Odpowiedź ma być krótka, konkretna i w moim stylu.
    
    TREŚĆ NOWEGO MAILA:
    {email_content}
    """
    
    try:
        response = client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
        return response.text
    except Exception as e:
        print(f"Błąd Gemini: {e}")
        return None

def process_and_reply():
    """Główna pętla asystenta."""
    if args.dry_run:
        print("\n🚀 [DRY-RUN MODE] Tryb testowy aktywny.\n")

    # Pobieramy style z limitem z flagi
    style_examples = fetch_my_style_emails(args.limit_style)
    
    print(f"📩 Sprawdzam nowe wiadomości (limit odpowiedzi: {args.limit_replies})...")
    inbox_response = run_gws([
        'gmail', 'users', 'messages', 'list',
        '--params', f'{{"userId": "me", "q": "is:unread in:inbox", "maxResults": {args.limit_replies}}}'
    ])

    messages = inbox_response.get('messages', []) if inbox_response else []
    
    if not messages:
        print("😴 Brak nowych wiadomości.")
        return

    for msg in messages:
        msg_id = msg['id']
        message_data = run_gws(['gmail', 'users', 'messages', 'get', '--params', f'{{"userId": "me", "id": "{msg_id}"}}'])
        
        if not message_data: continue

        headers = message_data.get('payload', {}).get('headers', [])
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Nieznany")
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Wiadomość")
        
        print(f"🤖 Analizuję maila od: {sender}")
        reply_text = generate_reply(message_data.get('snippet', ''), style_examples)
        
        if not reply_text: continue

        print(f"📝 Wygenerowana odpowiedź dla {sender}:")
        print("-" * 30)
        print(reply_text)
        print("-" * 30)

        if args.dry_run:
            print(f"⏩ [DRY-RUN] Pominięto wysyłkę do {sender}.\n")
            continue

        # Przygotowanie i wysyłka
        reply_email = EmailMessage()
        reply_email.set_content(reply_text)
        reply_email['To'] = sender
        reply_email['Subject'] = subject if subject.startswith("Re:") else f"Re: {subject}"
        raw_msg = base64.urlsafe_b64encode(reply_email.as_bytes()).decode('utf-8')

        run_gws([
            'gmail', 'users', 'messages', 'send',
            '--params', '{"userId": "me"}',
            '--json', json.dumps({'raw': raw_msg, 'threadId': message_data['threadId']})
        ])

        run_gws([
            'gmail', 'users', 'messages', 'modify',
            '--params', f'{{"userId": "me", "id": "{msg_id}"}}',
            '--json', '{"removeLabelIds": ["UNREAD"]}'
        ])
        print(f"✅ Odpowiedź wysłana do {sender}.\n")

if __name__ == '__main__':
    process_and_reply()