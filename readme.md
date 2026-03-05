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
| `--dry-run` | Shows responses in console without sending. Perfect for testing. | `False` |
| `--limit-style` | Number of sent emails to fetch for style learning. | `3` |
| `--limit-replies` | Maximum number of replies to send in one cycle. | `1` |
| `--debug` | Saves detailed logs to `debug.log` (incoming emails and generated replies). | `False` |

### Flag Details

#### `--dry-run`
Test mode that generates replies but doesn't send them. Use this to:
- Verify the AI is generating appropriate responses
- Test your style learning configuration
- Preview responses before going live

#### `--limit-style`
Controls how many of your sent emails are analyzed to learn your writing style. Higher values provide better style mimicking but take longer to process.
- **Recommended**: 5-10 for best results
- **Minimum**: 3 for basic style learning

#### `--limit-replies`
Limits how many emails the script will respond to in a single run. Useful for:
- Rate limit management (Gmail API has quotas)
- Gradual rollout of automation
- Testing with small batches

#### `--debug`
Enables detailed logging to `debug.log` file with timestamps. Logs include:
- Full content of incoming emails (sender, subject, body)
- Generated AI responses
- Success/failure status of each operation
- API errors and warnings

**⚠️ Important**: Debug logs may contain sensitive information. Never commit `debug.log` to version control.

### Example Commands

**Safe test (recommended first run):**
```bash
python respond_emails.py --dry-run --limit-style 5
```

**Production run with limited replies:**
```bash
python respond_emails.py --limit-replies 3
```

**Debug mode for troubleshooting:**
```bash
python respond_emails.py --debug --dry-run
```

**Full production with logging:**
```bash
python respond_emails.py --debug --limit-style 10 --limit-replies 5
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