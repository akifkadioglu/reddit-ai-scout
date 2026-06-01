# Reddit AI Scout

Kullanıcının girdiği kelimeye göre Reddit'ten veri çeker. Opsiyonel OpenAI desteğiyle akıllı arama + özet.

## Kurulum

```bash
# Makefile ile (önerilen)
make setup

# veya elle
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sırlar:

```bash
cp .env.example .env              # Windows: copy .env.example .env
# .env içine OPENAI_API_KEY yaz
```

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

## Doğrudan Python ile

Makefile kullanmak istemezsen önce `source venv/bin/activate` ile ortamı aç, sonra `main.py`'yi kelimeyle çağır. `--limit` ile sonuç sayısını, `--ai` bayrağıyla OpenAI desteğini kontrol edersin.

## Yapı

```
reddit-ai-scout/
├── src/
│   ├── reddit_client.py   # Reddit public JSON API
│   ├── openai_client.py   # OpenAI akıllı arama/özet
│   └── config.py          # .env yükleme
├── main.py                # Giriş noktası
├── Makefile               # setup / run / clean
└── requirements.txt
```

## Notlar

- Reddit public JSON = OAuth yok, sadece `User-Agent` lazım. Ağır kullanım için resmi OAuth + PRAW geç.
- OpenAI opsiyonel: `--ai`/`AI=1` + `.env`'de anahtar varsa devreye girer, yoksa düz arama yapar.
- `.env` git'e girmez (`.gitignore` korur). Sırlar tek yerde (`src/config.py`).
