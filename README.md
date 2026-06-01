# Reddit AI Scout

Bir kelimeyi Reddit'te araştırır, gerçek tartışmalardan blog konuları üretir ve SEO odaklı tam blog yazısı + görselleri oluşturur.

İki kullanım yolu var:

1. **`/generate-blog` (Claude command — ana yol)** — uçtan uca, interaktif. Reddit araştırması → konu seçimi → tam SEO blog + görseller. **OpenAI gerektirmez** (sorgu + konu üretimini Claude yapar). Görseller için `GEMINI_API_KEY` ister.
2. **`make run` (standalone CLI)** — sadece Reddit araştırıp 10 blog konusu listeler (`result/<kelime>.md`). Bu **AI mode** OpenAI ister. OpenAI'sız varyantı: `make run-raw`.

## Kurulum

```bash
# Makefile ile (önerilen) — venv + paketler + browser indirir
make setup

# veya elle
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium       # Reddit erişimi icin browser
```

Ayarlar:

```bash
cp .env.example .env              # Windows: copy .env.example .env
# /generate-blog icin: GEMINI_API_KEY yaz (gorsel adimi)
# make run (AI mode) icin: OPENAI_API_KEY yaz (opsiyonel)
# REDDIT_COOKIE_BROWSER'i kendi tarayicina gore ayarla
```

## .env Değişkenleri

| Değişken                | Açıklama                                                          | Gerekli mi                 | Default       |
|-------------------------|------------------------------------------------------------------|----------------------------|---------------|
| `GEMINI_API_KEY`        | Görsel üretimi (cover + içerik) — `/generate-blog` görsel adımı  | `/generate-blog` için evet | —             |
| `OPENAI_API_KEY`        | Sorgu + konu üretimi — **sadece `make run` (AI mode)**           | Opsiyonel                  | —             |
| `OPENAI_MODEL`          | Kullanılacak OpenAI modeli (sadece AI mode)                      | Opsiyonel                  | `gpt-4o-mini` |
| `OUTPUT_LANG`           | `make run` çıktı dili — locale kodu (`en_US`, `tr_TR`…)          | Opsiyonel                  | `en_US`       |
| `REDDIT_COOKIE_BROWSER` | Cookie okunacak tarayıcı (`chrome/arc/brave/edge/…`)             | Opsiyonel                  | `chrome`      |

> `/generate-blog` komutu **OpenAI kullanmaz**: sorgu optimizasyonu ve konu üretimi Claude tarafında yapılır. Python yalnız Reddit'i kazımak için çalışır.

## `/generate-blog` Komutu (ana yol)

Tanım: `.agents/commands/generate-blog.md`. Üstündeki **CONFIG** bloğunu doldur (marka adı, yazar havuzu, kategori whitelist) — gerisi generic.

Akış (plan modu gibi adım adım sorar):

```
/generate-blog <locale> <keyword>     # locale opsiyonel, default en
```

1. **Araştırma** — Claude keyword'ü Reddit sorgusuna çevirir, `main.py "<sorgu>" --raw` ile postları çeker.
2. **Konu seç** — gerçek tartışmalardan ~10 blog konusu listeler; numara seçersin ya da kendi başlığını yazarsın.
3. **Ekleme** — "eklemek istediğin bir şey var mı?" diye sorar (açı, hedef kitle, ton, uzunluk…).
4. **Üret** — tam SEO blog yazısını `content/blog/<locale>/<slug>.md` olarak yazar.
5. **Görseller** — `scripts/generate-blog-images.sh` ile cover + içerik görsellerini üretir (`GEMINI_API_KEY`).

## Reddit'e Nasıl Erişiyor

Reddit, düz HTTP script'lerini çoğu IP'de **403** ile blokluyor. Bu yüzden araç **gerçek bir tarayıcı (Playwright)** kullanır: normal Reddit sayfasına uğrar, sonra `.json` adreslerinden veriyi okur.

### Otomatik cookie (block'u geçer)

Araç **zaten login olduğun yerel tarayıcının** Reddit cookie'lerini otomatik okur ve enjekte eder — `make login` yapmana gerek yok. Hangi tarayıcı: `.env` içindeki `REDDIT_COOKIE_BROWSER` (`chrome/arc/brave/edge/vivaldi/firefox/safari`).

> **Not:** Reddit, `HeadlessChrome` UA'sını blokluyor; araç bunu normal Chrome UA'sıyla maskeler, böylece **headless** (pencere açılmadan, sessiz) çalışır.

> **macOS:** İlk çalıştırmada tarayıcı cookie'lerini okumak için **Keychain izin penceresi** çıkar — **Allow**'a bas (tek seferlik). Cookie okunamazsa araç misafir moda düşer, uyarı basar (çökmez).

### Login gerekirse (opsiyonel)

Otomatik cookie de yetmezse (`All Reddit hosts returned a block page`), bir kere giriş yapmak çözer:

```bash
make login
```

Görünür tarayıcı açılır, giriş yap, terminale dönüp **Enter**'a bas. Oturum `.reddit_profile/` içine kaydedilir. Yine olmuyorsa farklı ağ/VPN dene.

## venv Moduna Geçme

Komutları `python main.py ...` diye doğrudan çalıştıracaksan önce sanal ortama gir. Prompt başında `(venv)` görürsen içerdesin.

```bash
source venv/bin/activate          # macOS / Linux
venv\Scripts\Activate.ps1         # Windows (PowerShell)
deactivate                        # çıkış
```

Not: Makefile hedefleri (`make run` vb.) venv'i kendi bulur — onlar için aktivasyon gerekmez.

## Makefile (standalone CLI)

`make run` ve `make run-raw` hedeflerinde `q` parametresi **zorunlu** — arama kelimen. Opsiyoneller: `LIMIT` (kaç Reddit sonucu, default 10), `TOPICS` (kaç blog konusu, default 10; sadece AI mode). Parametreleri `isim=değer` biçiminde eklersin; kelimede boşluk varsa tırnak içine al.

### Parametreler

| Parametre  | Açıklama                                  | Default |
|------------|-------------------------------------------|---------|
| `q`        | Arama kelimesi (zorunlu)                  | —       |
| `LIMIT`    | Çekilecek Reddit sonuç sayısı             | 10      |
| `TOPICS`   | Üretilecek blog konusu sayısı (AI mode)   | 10      |

### Hedefler

| Hedef          | Ne yapar                                                       | OpenAI |
|----------------|----------------------------------------------------------------|--------|
| `make setup`   | venv + paketler + browser kur                                  | —      |
| `make login`   | Reddit'e giriş (opsiyonel, blok yersen)                        | —      |
| `make run`     | Araştır + **10 blog konusu üret** (`q` zorunlu)                | gerekir|
| `make run-raw` | Araştır + **ham Reddit postlarını dök** (konu üretmez)         | gerekmez|
| `make clean`   | venv + `__pycache__` sil                                       | —      |

## Kullanım Örnekleri

```bash
# AI mode: 10 konu uretir (OPENAI_API_KEY gerekir)
make run q="instagram dm automation"
make run q="bitcoin" LIMIT=15 TOPICS=8

# Raw mode: sadece Reddit postlari (OpenAI gerekmez)
make run-raw q="machine learning" LIMIT=15
```

Doğrudan Python ile (önce venv'e gir):

```bash
source venv/bin/activate

python main.py "bitcoin" --limit 15 --topics 8     # AI mode
python main.py "bitcoin" --raw --limit 15          # raw, OpenAI'siz
```

## Çıktı

- **`make run` (AI mode):** `result/<kelime>.md` — `# Blog Topic Ideas` başlığı, numaralı **10 blog konusu** (`OUTPUT_LANG` dilinde) + kaynak Reddit linkleri.
- **`make run-raw` / `--raw`:** `result/<kelime>.md` — `# Reddit Research` başlığı, ham post listesi + subreddit'ler (konu üretmez).
- **`/generate-blog`:** `content/blog/<locale>/<slug>.md` tam SEO blog yazısı + `public/images/blogs/...` altında üretilmiş görseller.

## Yapı

```
reddit-ai-scout/
├── .agents/commands/
│   └── generate-blog.md       # /generate-blog komutu (CONFIG + tum kurallar)
├── scripts/
│   └── generate-blog-images.sh # IMAGE_PROMPT bloklarindan gorsel uretir (Gemini)
├── src/
│   ├── reddit_client.py        # Reddit scraper (Playwright + tarayici cookie enjekte)
│   ├── openai_client.py        # Sorgu optimize + konu uretimi (sadece AI mode)
│   ├── login.py                # Bir kerelik Reddit girisi (opsiyonel)
│   └── config.py               # .env yukleme
├── main.py                     # CLI — AI mode | --raw mode
├── result/                     # make run/run-raw ciktilari (<kelime>.md)
├── Makefile                    # setup / login / run / run-raw / clean
└── requirements.txt
```

## Notlar

- Reddit verisi gerçek tarayıcı (Playwright) ile çekilir — OAuth/API anahtarı yok. `make setup` browser'ı da indirir; elle kurarken `playwright install chromium` çalıştır.
- `/generate-blog` **OpenAI istemez**; `OPENAI_API_KEY` yalnız standalone `make run` (AI mode) için gerekir. Sadece komutu kullanacaksan `.env`'den çıkarabilirsin.
- Görsel üretimi `GEMINI_API_KEY` ister; anahtar yoksa script uyarır.
- `.env` ve `.reddit_profile/` git'e girmez (`.gitignore` korur).
