from engines.llm.ollama_client import generate

def translate_text(text: str, lang: str):

    prompt = f"""
    Translate the following Sanskrit text into {lang}.
    Provide:
    1. Literal meaning
    2. Contextual meaning

    Text:
    {text}
    """

    output = generate(prompt)

    return {
        "translation": output,
        "confidence": 0.75  # placeholder for now
    }