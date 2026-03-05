# 🤖 AI Gmail Autoresponder (Gemini + GWS CLI)

Automatyczny asystent e-mailowy, który analizuje Twój styl komunikacji na podstawie wysłanych wiadomości i odpowiada na nowe maile, korzystając z bazy wiedzy na stronie `dev.orpi.pl`.

## 🌟 Funkcje

- **Naśladowanie Stylu**: Analizuje Twoje wysłane wiadomości, aby zachować Twój ton i strukturę maila.
- **Baza Wiedzy**: Wykorzystuje stronę `dev.orpi.pl` jako źródło informacji przy odpowiedziach.
- **Tryb Dry-Run**: Pozwala testować odpowiedzi w konsoli bez ich wysyłania.
- **Parametryzacja**: Możliwość określenia liczby maili do nauki stylu oraz liczby odpowiedzi.

## 🛠️ Wymagania

- **Python 3.11+**
- **Google Workspace CLI (gws)**: Zainstalowane globalnie (`npm install -g @googleworkspace/cli`).
- **Google Cloud CLI (gcloud)**: Do autoryzacji.
- **Gemini API Key**: Z Google AI Studio.

## 🚀 Instalacja i Konfiguracja

### 1. Autoryzacja Gmail

```bash
gcloud auth login
gws auth setup --scopes "https://www.googleapis.com/auth/gmail.modify"
```

### 2. Eksport kluczy (Wymagane na macOS)

```bash
gws auth export --unmasked > credentials.json
```

### 3. Środowisko Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install google-genai python-dotenv
```

### 4. Plik .env

Utwórz plik `.env` i dodaj:

```env
GEMINI_API_KEY=twoj_klucz_api
GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=credentials.json
```

## 🎮 Sposób użycia

Skrypt obsługuje następujące flagi:

| Flaga | Opis | Domyślnie |
|-------|------|-----------|
| `--dry-run` | Pokazuje odpowiedzi w konsoli bez wysyłania. | False |
| `--limit-style` | Liczba maili pobieranych do nauki stylu. | 3 |
| `--limit-replies` | Maksymalna liczba odpowiedzi w jednym cyklu. | 1 |

### Przykłady komend

**Bezpieczny test:**
```bash
python respond_emails.py --dry-run --limit-style 5
```

**Uruchomienie produkcyjne:**
```bash
python respond_emails.py --limit-replies 3
```

## 🧠 Mechanizm działania

1. **Analiza Stylu**: Pobiera n wysłanych wiadomości przez gws.
2. **Generowanie**: Gemini 2.0 Flash tworzy odpowiedź łącząc styl z faktami z dev.orpi.pl.
3. **Wysyłka**: Skrypt wysyła odpowiedź w tym samym wątku i oznacza maila jako przeczytany.

## 🔒 Bezpieczeństwo

Dodaj poniższe pliki do `.gitignore`:

```
.env
credentials.json
venv/
```

## 📄 Licencja

Projekt udostępniony na licencji MIT.