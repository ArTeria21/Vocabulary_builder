# Vocabulary Builder Bot

Telegram bot for creating Quizlet flashcards using the **Contextual Immersion** method (inspired by Marina Gorskaya). Cards are generated with definitions, collocations, and gap-fill examples — all in the target language, no translations.

## Methodology

**Contextual Immersion** teaches vocabulary through:
- Clear definitions in the target language
- Synonyms and parts of speech
- Collocations (common phrases)
- Gap-fill example sentences

**Card Format:**
- *Side 1 (Term):* The word/phrase
- *Side 2 (Definition):* Definition + Collocations + Gap-fill examples (all in target language)

## Commands

| Command | Description |
|---------|-------------|
| `/en <word>` | Generate card for English word (B2-C1 level) |
| `/de <word>` | Generate card for German word (A1-A2 beginner level) |
| `/dump_english` | Export English cards as .txt for Quizlet & clear buffer |
| `/dump_german` | Export German cards as .txt for Quizlet & clear buffer |
| `/stats` | View statistics (cards in buffer, unique words, total history) |

## Workflow

1. Send a word with `/en word` or `/de word`
2. Bot generates a card with definition, collocations, and examples
3. Review the card and click:
   - ✅ **Accept** - Add to buffer
   - ❌ **Decline** - Discard the card
   - 🔄 **Regenerate** - Get a new version
4. Use `/dump_english` or `/dump_german` to export for Quizlet
5. Import the .txt file to Quizlet using "Custom Import"

## Output Format

The bot generates `.txt` files optimized for Quizlet Custom Import:
- **Card Separator:** `####`
- **Field Separator:** Tab (`\t`)

Example:
```
indecisive	adj. Not able to make decisions quickly and effectively. (Syn: hesitant, unsure)

Collocations:
- a weak and _____ man
- proved to be _____ about the matter

Examples:
- He was too _____ to carry out his political program.
- I am exceedingly _____ about what to wear.####
```

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
