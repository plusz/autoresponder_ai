# 🤖 AI Gmail Autoresponder (Gemini + GWS CLI)

An automated email assistant that analyzes your communication style based on sent messages and responds to new emails using the knowledge base from `dev.orpi.pl`.

## 🌟 Features

- **Style Mimicking**: Analyzes your sent messages to preserve your tone and email structure.
- **Knowledge Base**: Uses the `dev.orpi.pl` website as a source of information for responses.
- **Dry-Run Mode**: Allows testing responses in the console without sending them.
- **Parameterization**: Ability to specify the number of emails for style learning and the number of replies.

## 🛠️ Requirements

- **Python 3.11+**
- **Google Workspace CLI (gws)**: Installed globally (`npm install -g @googleworkspace/cli`).
- **Google Cloud CLI (gcloud)**: For authorization.
- **Gemini API Key**: From Google AI Studio.

## 🚀 Installation and Configuration

### 1. Gmail Authorization

```bash
gcloud auth login
gws auth setup --scopes "https://www.googleapis.com/auth/gmail.modify"
```

### 2. Export Credentials (Required on macOS)

```bash
gws auth export --unmasked > credentials.json
```

### 3. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install google-genai python-dotenv
```

### 4. .env File

Create a `.env` file and add:

```env
GEMINI_API_KEY=your_api_key
GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=credentials.json
```

## 🎮 Usage

The script supports the following flags:

| Flag | Description | Default |
|------|-------------|---------|
| `--dry-run` | Shows responses in console without sending. | False |
| `--limit-style` | Number of emails fetched for style learning. | 3 |
| `--limit-replies` | Maximum number of replies in one cycle. | 1 |
| `--debug` | Saves detailed logs to `debug.log` (incoming emails and replies). | False |

### Example Commands

**Safe test:**
```bash
python respond_emails.py --dry-run --limit-style 5
```

**Production run:**
```bash
python respond_emails.py --limit-replies 3
```

**Debug mode (logs all email details):**
```bash
python respond_emails.py --debug --dry-run
```

## 🧠 How It Works

1. **Style Analysis**: Fetches n sent messages via gws.
2. **Generation**: Gemini 2.0 Flash creates a response combining style with facts from dev.orpi.pl.
3. **Sending**: The script sends the response in the same thread and marks the email as read.

## 🔒 Security

Add the following files to `.gitignore`:

```
.env
credentials.json
venv/
debug.log
```

## 📄 License

Project released under the MIT License.