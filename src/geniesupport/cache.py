"""Answer cache: reuse answers for repeated questions to save cost."""
_cache = {}   # normalized question -> full result dict

def _key(question: str) -> str:
    return question.strip().lower()

def get_cached(question: str):
    return _cache.get(_key(question))

def put_cache(question: str, result: dict):
    _cache[_key(question)] = result