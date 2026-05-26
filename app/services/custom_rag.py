from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#  LLM here will ONLY be used for chat and normal answers , will use booking.py FOR booking 
def get_answer(query: str, context_chunks: list[str], history: list[dict]) -> str:

    context = "\n\n".join(context_chunks)
    system_prompt = f"""You are an assistant for answering queries based on the uploaded context. Answer using CONTEXT only. If unsure, say: "I don't know."
        CONTEXT: {context}"""

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": query}]
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.2,
        max_tokens=150,
    )

    return response.choices[0].message.content