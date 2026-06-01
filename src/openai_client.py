"""OpenAI API istemcisi — arama kelimesini akıllıca genişletir/özetler."""
from openai import OpenAI

from .config import require_openai_key, OPENAI_MODEL


def _get_client() -> OpenAI:
    """OpenAI istemcisini anahtarla başlat."""
    return OpenAI(api_key=require_openai_key())


def expand_query(keyword: str) -> str:
    """Kullanıcı kelimesini Reddit araması için iyi sorguya çevir."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kullanıcı '{keyword}' arıyor. Reddit'te en alakalı sonuçları "
                    f"bulmak için kısa, optimize bir arama sorgusu üret. "
                    f"Sadece sorguyu döndür, açıklama yok."
                ),
            }
        ],
    )
    return resp.choices[0].message.content.strip()


def summarize_results(keyword: str, posts: list[dict]) -> str:
    """Reddit sonuçlarını OpenAI ile özetle."""
    client = _get_client()
    titles = "\n".join(f"- {p['title']} (r/{p['subreddit']})" for p in posts)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kullanıcı '{keyword}' hakkında araştırıyor. "
                    f"Şu Reddit başlıklarına göre kısa Türkçe özet çıkar:\n\n{titles}"
                ),
            }
        ],
    )
    return resp.choices[0].message.content.strip()
