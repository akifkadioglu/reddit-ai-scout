"""Reddit AI Scout — kelimeye göre Reddit'ten veri çeker, OpenAI ile zenginleştirir."""
import argparse

from src import reddit_client, openai_client
from src.config import OPENAI_API_KEY


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit AI Scout")
    parser.add_argument("keyword", help="Aranacak kelime")
    parser.add_argument("--limit", type=int, default=10, help="Sonuç sayısı")
    parser.add_argument(
        "--ai", action="store_true", help="OpenAI ile akıllı arama + özet"
    )
    args = parser.parse_args()

    query = args.keyword

    # OpenAI ile sorguyu genişlet (anahtar varsa ve --ai verildiyse)
    if args.ai and OPENAI_API_KEY:
        query = openai_client.expand_query(args.keyword)
        print(f"[OpenAI] Optimize sorgu: {query}\n")
    elif args.ai:
        print("[Uyarı] OPENAI_API_KEY yok, düz arama yapılıyor.\n")

    # Subreddit ara
    print("=== Subreddit'ler ===")
    for sub in reddit_client.search_subreddits(query, args.limit):
        print(f"  r/{sub['name']} — {sub['subscribers']} abone")

    # Gönderi ara
    print("\n=== Gönderiler ===")
    posts = reddit_client.search_posts(query, args.limit)
    for p in posts:
        print(f"  [{p['score']}] {p['title']}\n      {p['url']}")

    # OpenAI özeti
    if args.ai and OPENAI_API_KEY and posts:
        print("\n=== OpenAI Özet ===")
        print(openai_client.summarize_results(args.keyword, posts))


if __name__ == "__main__":
    main()
