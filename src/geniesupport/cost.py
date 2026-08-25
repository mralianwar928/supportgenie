from src.geniesupport.config import PRICE_INPUT_PER_1M, PRICE_OUTPUT_PER_1M

def extract_usage(response) -> tuple[int, int]:
    """Pull (prompt_tokens, completion_tokens) from a ChatGroq response."""
    usage = getattr(response, "response_metadata", {}).get("token_usage", {})
    return usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

def compute_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return ((prompt_tokens / 1_000_000) * PRICE_INPUT_PER_1M
            + (completion_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M)