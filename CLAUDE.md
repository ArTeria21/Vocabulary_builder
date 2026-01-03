# Project Concept
This project is a personal Telegram bot designed to create high-quality Quizlet flashcards for learning English and German. The core philosophy of the bot is based on the "Contextual Immersion" method (inspired by Marina Gorskaya). The bot avoids direct translation (e.g., English-Russian) and instead uses definitions, synonyms, and gap-fill context sentences in the target language to explain words.

# Core Logic & Philosophy
The bot acts as an expert linguist. When the user sends a word (Target Word), the bot must:
1.  **Identify the language** (English or German).
2.  **Analyze the word** using an LLM to find its most common meaning, collocations, and usage contexts.
3.  **Generate a Quizlet Card** strictly following this structure:
    * **Side 1 (Term):** The Target Word itself.
    * **Side 2 (Definition):** A multi-line rich explanation containing:
        * A clear, simple definition in the *Target Language* (NO translations to Russian/native language).
        * 2-3 Collocations (common phrases) containing the word.
        * 2-3 Example sentences where the Target Word is replaced by a placeholder (e.g., "_____").
4.  **Save** this data to a local buffer.

# Functionality
1.  **Single User:** The bot processes requests only for the specific user.
2.  **Data Storage:** Maintain two local CSV/buffer files: one for German, one for English.
3.  **Commands:**
    * `/start`: Greet the user and explain the methodology (No translations, context-based).
    * `/dump_german`: Generate and send a `.txt` file with all accumulated German cards, then clear the German buffer.
    * `/dump_english`: Generate and send a `.txt` file with all accumulated English cards, then clear the English buffer.
    * `/stats`: Show statistics:
        * Number of cards currently in buffer (English/German).
        * Number of unique words added since the last dump.
4.  **Word Processing:**
    * Accept a text message (word/phrase).
    * Generate the card content via LLM.
    * Reply with a confirmation: "Added [Word]. Created [X] cards." (Usually 1 card per word, unless the word has distinct multiple meanings requested).

# Output File Format (.txt)
The bot must generate a `.txt` file optimized for Quizlet's "Custom Import".
* **Card Separator:** `####`
* **Field Separator:** `\t` (Tab character)
* **Newlines:** The Definition field MUST support multi-line text (preserved in the text file).

**Example of the raw .txt content:**
```text
Indecisive	adj. Not able to make decisions quickly and effectively.
(Syn: hesitant, unsure)

Collocations:
- a weak and _____ man
- proved to be _____

Examples:
- He was too _____ to carry out his political program.
- I am exceedingly _____ about what to wear.####
Think outside the box	To think imaginatively using new ideas instead of traditional or expected ideas.

Examples:
- You need to be creative and be able to _____.
- We need to _____ to solve this problem.

```

# Tech Stack

* **Language:** Python 3.12
* **Bot Framework:** AIOgram (current version), fully asynchronous.
* **LLM Integration:** OpenAI API (Async client).
* **Configuration:** `pydantic-settings` for environment variables.
* **Dependency Manager:** UV.
* **Data Handling:** Pandas (optional, if helpful for buffer management) or standard file I/O.

# Coding Requirements

* **Simplicity:** Keep the codebase clean and minimal.
* **Documentation:** Use docstrings and type hinting (PEP 484) everywhere.
* **Asynchrony:** Ensure all I/O operations (LLM calls, file writes, Telegram updates) are async.
* **Prompt Engineering:** Ensure the System Prompt for the LLM explicitly forbids translations and enforces the "Definition + Gap-fill Examples" structure.