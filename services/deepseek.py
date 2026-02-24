import os
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
    return _client


SYSTEM_PROMPT = (
    "Ты — помощник, который создаёт структурированные саммари на русском языке. "
    "Саммари должно быть чётким, информативным и содержать ключевые идеи. "
    "Используй маркированные списки и разделы с заголовками где уместно."
)

MAX_CHARS = 60_000
CHUNK_SIZE = 50_000


async def _call_api(messages: list[dict]) -> str:
    response = await _get_client().chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


async def summarize(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return await _call_api([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Сделай саммари следующего текста:\n\n{text}"},
        ])

    # Chunked summarization for long texts
    chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    chunk_summaries = []
    for i, chunk in enumerate(chunks, 1):
        summary = await _call_api([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Сделай краткое саммари части {i} из {len(chunks)}:\n\n{chunk}"},
        ])
        chunk_summaries.append(f"**Часть {i}:**\n{summary}")

    combined = "\n\n".join(chunk_summaries)
    return await _call_api([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Объедини следующие саммари частей в одно финальное структурированное саммари:\n\n{combined}"},
    ])
