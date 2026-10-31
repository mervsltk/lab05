# Föy 05 — RDBMS Mimarisi ve ACID: Kırarak Öğrenme

Modern Veritabanı Yönetim Sistemleri — Laboratuvar teslim deposu.
Görevlerin tam açıklaması **Föy 05 PDF**'indedir; bu dosya kısa bir hatırlatmadır.

## Bu hafta

FıratFit ön ödemeli **ders kredisi** sistemine geçti (`krediler` tablosu).
ACID özelliklerini bu bakiyeler üzerinde, **iki psql oturumunu yan yana**
çalıştırarak bizzat test edeceksiniz: atomik transfer, kirli okuma denemesi,
tekrarlanamayan okuma, kayıp güncelleme ve dayanıklılık (restart) deneyi.

## Hızlı başlangıç

```bash
echo "230541001" > ogrno.txt              # kendi numaranız
docker compose up -d
python3 veri/uret.py 230541001            # kendi numaranız → 7 CSV
docker exec -i vtys-postgres psql -U vtys -d vtysdb < sql/sema_hazir.sql
# İki ayrı terminalde (Oturum A ve Oturum B):
docker exec -it vtys-postgres psql -U vtys -d vtysdb
```

## Depo yapısı

| Yol | Ne |
|---|---|
| `ogrno.txt` | Öğrenci numaranız (ilk iş: doldurun) |
| `sql/sema_hazir.sql` | Şema + veri + krediler — HAZIR, değiştirmeyin |
| `sql/g1_transfer.sql` | Görev 1 — atomik transfer transaction'ı |
| `sonuc/g1.txt` | Görev 1 — başarısız transfer transkripti |
| `sonuc/g2_kirli.txt` | Görev 2a — kirli okuma deneyi transkripti |
| `sonuc/g2_tekrar.txt` | Görev 2b — REPEATABLE READ deneyi transkripti |
| `sonuc/g3.txt` | Görev 3 — kayıp güncelleme + düzeltme transkripti |
| `sonuc/g4.txt` | Görev 4 — dayanıklılık deneyi transkripti |

Transkript = iki oturumda yazdığınız komutlar ve aldığınız çıktıların,
hangi oturumda olduğu belli olacak şekilde (`-- A:` / `-- B:` başlıklarıyla)
kopyalanmış hâli. Değerlendirici, transkriptlerdeki **size özel** kredi
değerlerini kontrol eder — deneyi gerçekten yapmadan bu değerler bilinemez.


## Push etmeden önce kendinizi kontrol edin

Değerlendiriciyi kendi bilgisayarınızda çalıştırabilirsiniz — GitHub'daki ile
**aynı dosya, aynı puan**:

```bash
docker compose run --rm kontrol
```

Ekrana görev görev puanınız ve eksikleriniz düşer. İlk çalıştırma birkaç
saniye sürer, sonrakiler ~2 saniye. Ayrıca bir şey kurmanız gerekmez; Docker
zaten kurulu.

**Önce burada tam puan alın, sonra push edin.** Her push GitHub'da sınıfın
ortak Actions kotasından dakika harcar; deneme-yanılmayı buraya taşırsanız
kota dönem sonuna kadar yeter.

## Teslim

```bash
git add ogrno.txt sql/ sonuc/
git commit -m "Foy 05 teslimi"
git push
```
