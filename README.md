# Reddit AI Scout

Kullanıcının girdiği kelimeye göre Reddit'ten veri çeker. Opsiyonel OpenAI desteğiyle akıllı arama + özet. Sonuçları `result/<kelime>.json` olarak kaydeder.

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

Sırlar:

```bash
cp .env.example .env              # Windows: copy .env.example .env
# .env içine OPENAI_API_KEY yaz
```

## Reddit'e Nasıl Erişiyor

Reddit, düz HTTP script'lerini (`requests`) çoğu IP'de **403** ile blokluyor. Bu yüzden veri **gerçek bir tarayıcı (Playwright)** üzerinden çekiliyor: araç headless Chrome açar, `reddit.com`'dan misafir oturum çerezi alır, sonra `.json` adreslerine gidip veriyi okur. OAuth/şifre gerekmez.

Yine de **"blocked by network security"** hatası alırsan IP'n Cloudflare'a takılıyordur. `.env`'de:

```env
REDDIT_HEADLESS=0
```

yaparsan görünür bir Chrome penceresi açılır — bu, bot tespitini geçme şansını artırır. Hâlâ olmuyorsa farklı bir ağ/VPN dene.

## venv Moduna Geçme

Komutları `python main.py ...` diye doğrudan çalıştırmak istersen önce sanal ortama girmen lazım. Bu, terminalini venv'in içine sokar; o oturumda `python` ve `pip` artık sistemdekini değil venv'dekini kullanır. Prompt'un başında `(venv)` görürsen içerdesin demektir.

```bash
# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (cmd)
venv\Scripts\activate.bat
```

Çıkmak için:

```bash
deactivate
```

Not: Makefile hedefleri (`make run` vb.) venv'i kendisi bulur — onlar için aktivasyona gerek yok. Aktivasyon sadece komutları elle çalıştıracaksan gerekli.

## Makefile Nasıl Kullanılır

Projeyi Makefile üzerinden yönetirsin; venv'i elle açıp komut ezberlemene gerek kalmaz. Üç temel iş var: kurmak, çalıştırmak, temizlemek.

İlk adım kurulum hedefidir. Bu hedef sanal ortamı yaratır ve `requirements.txt` içindeki tüm bağımlılıkları yükler. Repoyu klonladıktan sonra tek sefer çalıştırman yeterli.

İkinci adım çalıştırma hedefidir. Burada `q` parametresi zorunludur — arama kelimeni buraya yazarsın. `q` vermezsen Makefile çalışmaz, sana kullanım mesajı basıp durur. İki opsiyonel parametre daha var: `LIMIT` kaç sonuç döneceğini belirler (vermezsen 10 kabul edilir), `AI` parametresine `1` verirsen OpenAI devreye girer ve hem aramayı akıllandırır hem sonuçları özetler. `AI` vermezsen düz arama yapar.

Parametreleri hedefin yanına `isim=değer` biçiminde eklersin; sırası önemli değil. Kelimede boşluk varsa tırnak içine al.

Üçüncü adım temizleme hedefidir. Sanal ortamı ve Python cache klasörlerini siler; sıfırdan kurmak ya da repoyu küçültmek istediğinde işine yarar.

### Parametreler

| Parametre | Açıklama                  | Default |
|-----------|---------------------------|---------|
| `q`       | Arama kelimesi (zorunlu)  | —       |
| `LIMIT`   | Sonuç sayısı              | 10      |
| `AI=1`    | OpenAI'yi aç              | kapalı  |

### Hedefler

| Hedef        | Ne yapar                        |
|--------------|---------------------------------|
| `make setup` | venv kur + bağımlılıkları yükle |
| `make run`   | Arama çalıştır (`q` zorunlu)    |
| `make clean` | venv + `__pycache__` sil        |

## Kullanım Örnekleri

Makefile ile:

```bash
# En basit: tek kelime, düz arama
make run q="python"

# Çok kelimeli arama (tırnak şart)
make run q="machine learning"

# Sonuç sayısını sınırla
make run q="bitcoin" LIMIT=5

# OpenAI ile akıllı arama + özet
make run q="rust vs go" AI=1

# Hepsi birden
make run q="indie game dev" LIMIT=3 AI=1
```

Doğrudan Python ile (önce venv'e gir):

```bash
source venv/bin/activate

python main.py "python"                            # düz arama
python main.py "bitcoin" --limit 5                 # sonuç sınırlı
python main.py "rust vs go" --ai                   # OpenAI akıllı arama + özet
python main.py "indie game dev" --limit 3 --ai     # hepsi birden
```

## Çıktı

Her arama sonucu `result/<kelime>.json` olarak yazılır. JSON içinde: orijinal kelime, optimize sorgu, subreddit listesi, gönderiler ve (varsa) OpenAI özeti bulunur.

## Yapı

```
reddit-ai-scout/
├── src/
│   ├── reddit_client.py   # Reddit scraper (Playwright browser)
│   ├── openai_client.py   # OpenAI akıllı arama/özet
│   └── config.py          # .env yükleme
├── main.py                # Giriş noktası
├── result/                # Arama çıktıları (<kelime>.json)
├── Makefile               # setup / run / clean
└── requirements.txt
```

## Notlar

- Reddit verisi gerçek tarayıcı (Playwright) ile çekilir — OAuth/şifre yok. `make setup` browser'ı da indirir; elle kurarken `playwright install chromium` çalıştır.
- Blok yersen `.env`'de `REDDIT_HEADLESS=0` dene, sonra farklı ağ/VPN.
- OpenAI opsiyonel: `--ai`/`AI=1` + `.env`'de anahtar varsa devreye girer, yoksa düz arama yapar.
- `.env` git'e girmez (`.gitignore` korur). Sırlar tek yerde (`src/config.py`).
