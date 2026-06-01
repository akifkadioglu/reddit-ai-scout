# Reddit AI Scout

Girdiğin kelimeyi Reddit'te araştırır, gerçek tartışmalardan **10 blog konusu (başlık + açıklama)** üretir ve `result/<kelime>.md` olarak kaydeder. OpenAI **zorunludur**; çıktı dili `.env`'den ayarlanır.

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
# .env içine OPENAI_API_KEY yaz (zorunlu)
# OUTPUT_LANG ve REDDIT_COOKIE_BROWSER ayarla
```

## .env Değişkenleri

| Değişken                | Açıklama                                              | Default        |
|-------------------------|-------------------------------------------------------|----------------|
| `OPENAI_API_KEY`        | OpenAI anahtarı (**zorunlu**)                         | —              |
| `OPENAI_MODEL`          | Kullanılacak model                                    | `gpt-4o-mini`  |
| `OUTPUT_LANG`           | Çıktı dili — locale kodu (`en_US`, `tr_TR`, `de_DE`…) | `en_US`        |
| `REDDIT_COOKIE_BROWSER` | Cookie okunacak tarayıcı (`chrome/arc/brave/edge/…`)  | `chrome`       |

## Reddit'e Nasıl Erişiyor

Reddit, düz HTTP script'lerini çoğu IP'de **403** ile blokluyor. Bu yüzden araç **gerçek bir tarayıcı (Playwright)** kullanır: normal Reddit sayfasına uğrar, sonra `.json` adreslerinden veriyi okur.

### Otomatik cookie (block'u geçer)

Araç **zaten login olduğun yerel tarayıcının** Reddit cookie'lerini otomatik okur ve enjekte eder — `make login` yapmana gerek yok. Hangi tarayıcı: `.env` içindeki `REDDIT_COOKIE_BROWSER` (`chrome/arc/brave/edge/vivaldi/firefox/safari`).

> **Önemli:** Reddit **headless** tarayıcıyı `403` ile blokluyor. Çekim her zaman **görünür (headed)** çalışır — her `make run`'da kısa süre tarayıcı penceresi açılıp kapanır, bu normal.

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

## Makefile Nasıl Kullanılır

Üç temel iş: kurmak, çalıştırmak, temizlemek.

`make run` hedefinde `q` parametresi **zorunlu** — arama kelimen. İki opsiyonel parametre: `LIMIT` kaç Reddit sonucu çekileceği (default 10), `TOPICS` kaç blog konusu üretileceği (default 10). Parametreleri `isim=değer` biçiminde eklersin; kelimede boşluk varsa tırnak içine al.

### Parametreler

| Parametre  | Açıklama                       | Default |
|------------|--------------------------------|---------|
| `q`        | Arama kelimesi (zorunlu)       | —       |
| `LIMIT`    | Çekilecek Reddit sonuç sayısı  | 10      |
| `TOPICS`   | Üretilecek blog konusu sayısı  | 10      |

### Hedefler

| Hedef        | Ne yapar                                 |
|--------------|------------------------------------------|
| `make setup` | venv + paketler + browser kur            |
| `make login` | Reddit'e giriş (opsiyonel, blok yersen)  |
| `make run`   | Araştır + blog konuları üret (`q` zorunlu)|
| `make clean` | venv + `__pycache__` sil                 |

## Kullanım Örnekleri

Makefile ile:

```bash
# En basit: 10 sonuç, 10 blog konusu
make run q="instagram dm automation"

# Çok kelimeli arama (tırnak şart)
make run q="machine learning"

# Reddit sonuç ve konu sayısını ayarla
make run q="bitcoin" LIMIT=15 TOPICS=8
```

Doğrudan Python ile (önce venv'e gir):

```bash
source venv/bin/activate

python main.py "instagram dm automation"                  # 10 konu
python main.py "bitcoin" --limit 15 --topics 8            # ayarlı
```

## Çıktı

Her çalıştırma `result/<kelime>.md` olarak yazılır. Markdown içinde:

- `# Blog Topic Ideas: <kelime>` başlığı + optimize sorgu
- Numaralı **10 blog konusu** — her biri başlık + 1-2 cümle açıklama (`OUTPUT_LANG` dilinde)
- **Sources (Reddit)** — konuların türetildiği gerçek Reddit gönderilerinin linkleri

## Yapı

```
reddit-ai-scout/
├── src/
│   ├── reddit_client.py   # Reddit scraper (Playwright + tarayıcı cookie enjekte)
│   ├── openai_client.py   # Sorgu optimize + blog konusu üretimi
│   ├── login.py           # Bir kerelik Reddit girişi (opsiyonel)
│   └── config.py          # .env yükleme
├── main.py                # Giriş noktası — araştır + .md üret
├── result/                # Çıktılar (<kelime>.md)
├── Makefile               # setup / login / run / clean
└── requirements.txt
```

## Notlar

- Reddit verisi gerçek tarayıcı (Playwright) ile çekilir — OAuth/API anahtarı yok. `make setup` browser'ı da indirir; elle kurarken `playwright install chromium` çalıştır.
- OpenAI **zorunlu**: `.env`'de `OPENAI_API_KEY` yoksa araç hata verip durur.
- Çıktı dili `OUTPUT_LANG` ile belirlenir (örn. `tr_TR` → Türkçe). Reddit araması orijinal kalır, sadece üretilen blog konuları çevrilir.
- `.env` ve `.reddit_profile/` git'e girmez (`.gitignore` korur).
