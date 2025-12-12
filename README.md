# Vocabulary Builder Bot

Telegram bot for creating Quizlet flashcards using LLM-powered analysis.

## Commands

| Command | Description |
|---------|-------------|
| `/en <word>` | Add English word |
| `/de <word>` | Add German word |
| `/dump_english` | Export & clear English CSV |
| `/dump_german` | Export & clear German CSV |
| `/stats` | View statistics |

## Local Setup

```bash
cp .env.example .env   # Edit with your credentials
uv sync
uv run python main.py
```

## Docker Deployment (VPS)

```bash
# Clone and configure
git clone <repo-url> && cd Vocabulary_builder
cp .env.example .env   # Edit with your credentials

# Run
docker compose up -d --build

# Logs
docker compose logs -f

# Update
git pull && docker compose up -d --build

# Stop
docker compose down
```

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_token
ALLOWED_USER_ID=your_telegram_id
OPENROUTER_API_KEY=your_api_key
```
