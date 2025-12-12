# Vocabulary Builder Bot

A personal Telegram bot for creating Quizlet flashcards for learning English and German using LLM-powered analysis.

## Features

- 🤖 Process words/phrases using AI to create contextual flashcards
- 🇬🇧 English vocabulary with focus on phrasal verbs and collocations (B1-B2/FCE level)
- 🇩🇪 German vocabulary with focus on verb conjugations, noun gender, and plurals (A2 level)
- 📊 Track statistics on cards and unique words
- 📥 Export CSV files compatible with Quizlet import

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Create `.env` file:**
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ALLOWED_USER_ID=your_telegram_user_id
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

3. **Run the bot:**
   ```bash
   uv run python main.py
   ```

## Commands

- `/start` — Welcome message and help
- `/en <word>` — Add an English word (e.g., `/en useful`)
- `/de <word>` — Add a German word (e.g., `/de aufgeben`)
- `/dump_english` — Download English cards CSV and clear buffer
- `/dump_german` — Download German cards CSV and clear buffer
- `/stats` — View current statistics

## Usage

Send a word with the language command:
- `/en look forward to` — for English phrasal verbs
- `/de die Methode` — for German nouns

The bot will:
1. Analyze meanings and usage contexts
2. Create 1-3 flashcards with fill-in-the-blank exercises
3. Add cards to the buffer for later export

## CSV Format

The exported CSV follows Quizlet's import format:
```csv
"Task with gap _____","Answer"
```
