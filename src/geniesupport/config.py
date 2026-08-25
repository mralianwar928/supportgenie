CHAT_MODEL = "openai/gpt-oss-20b"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
PERSIST_DIR = "data/chroma"

TOP_K = 4
RELEVANCE_THRESHOLD = 0.1     # below this → escalate. CALIBRATE against your data.
MAX_HISTORY_TURNS = 6          # bounded conversation memory

# Groq pricing for gpt-oss-20b, per 1M tokens (check console.groq.com for current rates)
PRICE_INPUT_PER_1M = 0.075
PRICE_OUTPUT_PER_1M = 0.30