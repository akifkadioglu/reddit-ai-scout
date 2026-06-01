# Reddit AI Scout

Bir kelimeyi Reddit'te araştırır, gerçek tartışmaları Markdown olarak döker; bu da SEO odaklı blog konusu keşfini besler. Tamamen JavaScript (npm paketi), Reddit'in 403 anti-bot bloğunu Puppeteer ile aşar.

İki kullanım yolu var:

1. **`/generate-blog` (Claude command — ana yol)** — uçtan uca, interaktif. Reddit araştırması → konu seçimi → tam SEO blog + görseller. **OpenAI gerektirmez** (sorgu + konu üretimini Claude yapar). Görseller için `GEMINI_API_KEY` ister.
2. **`reddit-scout` (standalone CLI)** — sadece Reddit'i araştırıp ham postları + subreddit'leri `.previous/<kelime>.md` olarak yazar. AI yok, anahtar gerekmez.

## Kurulum

```bash
npm i                 # puppeteer + stealth + bundled Chromium indirir
cp .env.example .env  # görseller için GEMINI_API_KEY yaz
```

Node >= 20.6 gerekir (`.env` için `process.loadEnvFile`).

## CLI

```bash
npx reddit-scout "instagram dm automation"            # .previous/<kelime>.md yazar
npx reddit-scout "bitcoin trading" --limit 15
```

Çıktı `.previous/<kelime>.md`:

```
# Reddit Research: <kelime>

_Query: `<sorgu>` — N posts across M subreddits. No AI applied; topic ideas are generated downstream._

## Posts
- [başlık](url) — r/subreddit (skor pts)
...

## Subreddits
- r/isim (abone subs) — açıklama
...
```

## .env Değişkenleri

| Değişken             | Açıklama                                          | Gerekli mi                 | Default          |
|----------------------|---------------------------------------------------|----------------------------|------------------|
| `GEMINI_API_KEY`     | Görsel üretimi — `/generate-blog` görsel adımı    | `/generate-blog` için evet | —                |
| `IMG_ASPECT`         | Görsel en-boy oranı                               | Opsiyonel                  | `16:9`           |
| `IMG_WIDTH`          | Görsel genişliği (px, macOS `sips` ile)           | Opsiyonel                  | `1200`           |
| `IMG_HEIGHT`         | Görsel yüksekliği (px, macOS `sips` ile)          | Opsiyonel                  | `630`            |
| `REDDIT_COOKIE_TTL_MS`| Guest cookie cache ömrü (ms)                     | Opsiyonel                  | `21600000` (6s)  |

## `/generate-blog` Komutu (ana yol)

Tanım: `.claude/commands/generate-blog.md`. Üstündeki **CONFIG** bloğunu doldur (marka adı, yazar havuzu, kategori whitelist) — gerisi generic.

```
/generate-blog <locale> <keyword>     # locale opsiyonel, default en
```

1. **Araştırma** — Claude keyword'ü Reddit sorgusuna çevirir, `npx reddit-scout "<sorgu>"` ile postları çeker.
2. **Konu seç** — gerçek tartışmalardan 4 blog konusu sunar; arrow-key ile seçersin ya da kendi başlığını yazarsın.
3. **Ekleme** — "eklemek istediğin bir şey var mı?" diye sorar (açı, hedef kitle, ton, uzunluk…).
4. **Üret** — tam SEO blog yazısını `content/blog/<locale>/<slug>.md` olarak yazar.
5. **Görseller** — Claude cover + içerik görsellerini `npx blog-image` ile doğrudan üretir (`GEMINI_API_KEY`).

## Reddit'e Nasıl Erişiyor

Reddit, düz HTTP isteklerini çoğu IP'de **403** ile blokluyor (stdlib `urllib` de, node `fetch` de). Araç bunu iki adımda aşar:

1. **Cookie hasadı (headless Chrome).** Bir kez headless Chrome (Puppeteer + stealth) reddit.com'a uğrar ve **guest cookie**'yi `page.cookies()` ile (httpOnly dahil) toplar. Cookie OS cache dizinine yazılır (`~/.cache/reddit-ai-scout/cookie.json`, Windows'ta `%LOCALAPPDATA%`). Consumer repo'su kirlenmez.
2. **İstekler (plain fetch).** Sonraki tüm aramalar düz `fetch` ile, cookie header'ı + aynı Chrome UA'sı kullanılarak yapılır — tarayıcı açılmaz, hızlıdır. Cookie `REDDIT_COOKIE_TTL_MS` (default 6 saat) sonrası bayatlayınca otomatik yeniden hasat edilir.

> **Not:** Reddit `HeadlessChrome` UA'sını blokluyor; hasat hem de fetch aynı normal Chrome UA'sını kullanır (UA tutarsızlığı tek başına 403 sebebi).

Bir istek blok yerse (JSON yerine HTML duvar) cookie **bir kez** zorla yenilenip tekrar denenir. Anti-bot **flagged IP**'lerde (datacenter/VPN) guest cookie yine yetmeyebilir — bu durumda net hata döner; temiz bir ağ dene (interaktif login akışı yok).

## Programatik Kullanım (devDependency)

```bash
npm i -D reddit-ai-scout
```

```js
import { search } from "reddit-ai-scout";

const { subreddits, posts } = await search("instagram dm automation", 10);
// posts:      [{ title, subreddit, score, url }, ...]
// subreddits: [{ name, subscribers, description }, ...]
```

İlk çağrıda cookie headless Chrome ile hasat edilip cache'lenir; sonraki çağrılar cache'ten plain fetch ile döner.

## Görsel CLI (blog-image)

`/generate-blog` her görsel için bunu çağırır; elle de çalıştırabilirsin:

```bash
PROMPT='bright modern home office, no text, no logos' \
OUT='public/images/blogs/my-post/cover.jpg' \
npx blog-image
```

Gemini `gemini-2.5-flash-image` (Nano Banana) ile üretir, `OUT` zaten varsa atlar (idempotent). macOS'ta `sips` ile tam piksele resize eder; başka sistemde API oranında kalır.

## Yapı

```
reddit-ai-scout/
├── .claude/commands/
│   └── generate-blog.md       # /generate-blog komutu (CONFIG + kurallar)
├── bin/
│   ├── reddit-scout.js         # CLI: araştırma
│   └── blog-image.js           # CLI: Gemini görsel üretimi
├── src/
│   ├── cookie.js               # Guest cookie hasadı (headless) + OS cache
│   ├── reddit.js               # Reddit search (plain fetch + cookie)
│   └── markdown.js             # Markdown render + .previous/ çıktısı
├── .previous/                  # reddit-scout çıktıları (<kelime>.md)
├── package.json
└── .env.example
```

## Notlar

- Reddit cookie'si bir kez headless tarayıcı (Puppeteer) ile hasat edilir, sonra istekler plain fetch — OAuth/API anahtarı yok. `npm i` Chromium'u da indirir.
- `/generate-blog` **OpenAI istemez**; sorgu + konu üretimini Claude yapar.
- Görsel üretimi `GEMINI_API_KEY` ister; anahtar yoksa `blog-image` uyarır.
- Cookie cache consumer repo'suna değil OS cache dizinine yazılır; `.env` git'e girmez (`.gitignore` korur).
