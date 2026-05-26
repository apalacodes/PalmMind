from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#  LLM here will only be used for chat and normal answers , we will only use booking.py when a booking has been intitiated 
def get_answer(query: str,
    context_chunks: list[str],
    history: list[dict]
) -> str:

    context = "\n\n".join(context_chunks)
    system_prompt = f"""You are an assistant for answering queries based off of the uploaded context. Answer using CONTEXT only.
If unsure: "I don't know."
If user wants to book interview, ask for all details in ONE message: "Please provide your name, email, preferred date and time."
Once all four collected, say: BOOKING_READY

CONTEXT:
{context}"""


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