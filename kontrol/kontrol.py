#!/usr/bin/env python3
"""Föy 05 — Otomatik Değerlendirici

GitHub Actions içinde çalışır. Bu haftanın deneyleri iki oturumlu ve
etkileşimli olduğundan değerlendirme iki katmanlıdır:

  * Görev 1'in transfer transaction'ı gerçekten çalıştırılır ve bakiyeler
    KİŞİYE ÖZEL beklenen değerlerle karşılaştırılır.
  * Deney transkriptleri (Görev 2–4), deneyi gerçekten yapınca ortaya çıkan
    kişiye özel kredi değerleri ve anahtar komutlar üzerinden doğrulanır.

Beklenen değerler veri üretecinden Python ile hesaplanır; transkriptlerin
içerik kalitesi ve savunma asistana aittir.
"""
import os
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "veri"))
from uret import uret  # noqa: E402

try:
    import psycopg
except ImportError:
    print("HATA: psycopg kurulu değil (pip install 'psycopg[binary]').")
    sys.exit(2)

SONUCLAR = []

# Deney parametreleri (föyle birebir aynı olmalı)
TRANSFER_MIKTAR = 50      # G1: üye 1 → üye 2
KIRLI_ARTIS = 77          # G2a: üye 3
TEKRAR_ARTIS = 30         # G2b: üye 7
KAYIP_ARTIS = 10          # G3: üye 5, iki oturum da +10
DAYANIKLILIK_ARTIS = 40   # G4: üye 9


def kaydet(gorev, alinan, tam, mesaj):
    SONUCLAR.append((gorev, alinan, tam, mesaj))
    durum = "✓" if alinan == tam else ("~" if alinan > 0 else "✗")
    print(f"[{durum}] {gorev}: {alinan}/{tam} — {mesaj}")


def oku(yol):
    p = KOK / yol
    # is_file(): ogrenci bazen dosya yerine AYNI ADLA KLASOR olusturuyor
    # (ornegin "sonuc/g1.txt/g1.txt"). exists() bunu dosya sanip read_bytes()
    # ile cokuyor ve TUM degerlendirme sifirlaniyordu.
    if not p.is_file():
        return None
    try:
        ham = p.read_bytes()
    except OSError:
        return None
    # Windows'ta PowerShell'in ">" yonlendirmesi UTF-16 yazar; Not Defteri de
    # UTF-8'e BOM ekler. Bunlari cozmezsek ogrencinin dogru cikti dosyasi
    # taninmaz ve haksiz puan kaybi olur.
    if ham[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ham.decode("utf-16", errors="replace")
    return ham.decode("utf-8-sig", errors="replace")

def sql_kodu(metin):
    """SQL metninden yorumlari atar.

    Sablon dosyalarinin KENDI yorumlarinda "CREATE TABLE komutunuzu yazin"
    gibi ifadeler gectigi icin, ham metinde anahtar kelime aramak bos teslimi
    gecerli sayiyordu. Denetimler bu fonksiyonun ciktisi uzerinde yapilir.
    """
    metin = re.sub(r"/\*.*?\*/", " ", metin or "", flags=re.S)
    return re.sub("--.*", " ", metin)


def baglanti():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "vtys"),
        password=os.environ.get("PGPASSWORD", "vtys2026"),
        dbname=os.environ.get("PGDATABASE", "vtysdb"),
        autocommit=True,
    )


def ogrno_al():
    icerik = oku("ogrno.txt")
    if icerik is None:
        return None
    icerik = icerik.strip()
    return icerik if icerik.isdigit() else None


def sema_kur(con, t):
    ddl = (KOK / "sql" / "sema_hazir.sql").read_text(encoding="utf-8")
    ddl = re.sub(r"COPY[^;]+;", "", ddl)      # COPY'ler /veri yoluna bağlı
    con.execute(ddl)
    sira = [
        ("uyeler", ["uye_id", "ad", "dogum_yili"]),
        ("telefonlar", ["telefon_id", "uye_id", "numara"]),
        ("egitmenler", ["egitmen_id", "ad", "brans"]),
        ("salonlar", ["salon_id", "ad", "kapasite"]),
        ("dersler", ["ders_id", "ad", "egitmen_id", "salon_id", "ucret"]),
        ("kayitlar", ["kayit_id", "uye_id", "ders_id", "tarih"]),
        ("krediler", ["uye_id", "kredi"]),
    ]
    with con.cursor() as cur:
        for tablo, kolonlar in sira:
            with cur.copy(f"COPY {tablo} ({', '.join(kolonlar)}) FROM STDIN") as cp:
                for s in t[tablo]:
                    cp.write_row(tuple(s[k] for k in kolonlar))


def sayi_var(metin, deger):
    """Transkriptte değerin bağımsız bir sayı olarak geçip geçmediği."""
    return re.search(rf"(?<!\d){deger}(?!\d)", metin) is not None


# ------------------------------------------------------------- Görev 1
def transfer_calistir(con, sql):
    """Dosyadaki BEGIN...COMMIT bloklarini AYRI AYRI calistirir.

    Foy, Gorev 1'in 2. adiminda bilerek BASARISIZ olan bir transfer
    denemesi yaptiriyor (bakiyeden fazlasini aktarma). Ogrencilerin bir
    kismi bu denemeyi de ayni dosyaya yaziyor; dosyayi tek parca
    calistirinca CHECK kisiti patliyor ve DOGRU transfer de
    puanlanmiyordu. Bloklari tek tek calistirip hatali olani yutuyoruz:
    basarisiz blok zaten geri alinir, basarili olan uygulanir.

    Geriye yalnizca HIC blok uygulanamadiysa hata metni doner.
    """
    bloklar = re.findall(r"\bBEGIN\b.*?\bCOMMIT\b\s*;", sql,
                         re.IGNORECASE | re.S) or [sql]
    basarili, son_hata = False, None
    for blok in bloklar:
        try:
            con.execute(blok)
            basarili = True
        except Exception as e:
            son_hata = str(e).splitlines()[0]
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
    return None if basarili else son_hata


def kontrol_g1(con, kredi):
    sql = oku("sql/g1_transfer.sql")
    puan = 0
    mesajlar = []
    if not sql or "UPDATE" not in sql_kodu(sql).upper():
        kaydet("Görev 1 (Atomicity)", 0, 20,
               "sql/g1_transfer.sql bulunamadı veya UPDATE içermiyor.")
        return

    if re.search(r"\bBEGIN\b", sql, re.IGNORECASE) and \
       re.search(r"\bCOMMIT\b", sql, re.IGNORECASE):
        puan += 4
    else:
        mesajlar.append("Transfer bir BEGIN ... COMMIT bloğu içinde değil.")

    hata = transfer_calistir(con, sql)
    try:
        b1 = con.execute("SELECT kredi FROM krediler WHERE uye_id = 1").fetchone()[0]
        b2 = con.execute("SELECT kredi FROM krediler WHERE uye_id = 2").fetchone()[0]
        if b1 == kredi[1] - TRANSFER_MIKTAR and b2 == kredi[2] + TRANSFER_MIKTAR:
            puan += 12
            mesajlar.append("Transfer bakiyeleri doğru.")
        elif hata:
            mesajlar.append(f"Transfer çalıştırılamadı: {hata}")
        else:
            mesajlar.append("Transfer sonrası bakiyeler beklenenden farklı "
                            "(üye 1'den üye 2'ye tam 50 kredi geçmeli).")
    except Exception as e:
        mesajlar.append(f"Bakiyeler okunamadı: {str(e).splitlines()[0]}")

    icerik = oku("sonuc/g1.txt") or ""
    if re.search(r"violates check|check constraint|ihlal", icerik, re.IGNORECASE):
        puan += 4
        mesajlar.append("Başarısız transfer kanıtı yerinde.")
    else:
        mesajlar.append("sonuc/g1.txt'de CHECK kısıtı hatası görünmüyor "
                        "(bakiyeden fazla transfer denemesini yapıştırın).")
    kaydet("Görev 1 (Atomicity)", puan, 20, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 2
def kontrol_g2(kredi):
    puan = 0
    mesajlar = []

    kirli = oku("sonuc/g2_kirli.txt") or ""
    eski, yeni = kredi[3], kredi[3] + KIRLI_ARTIS
    if kirli and re.search(r"\bBEGIN\b", kirli, re.IGNORECASE) \
            and sayi_var(kirli, eski) and sayi_var(kirli, yeni):
        puan += 12
        mesajlar.append("Kirli okuma deneyi kanıtı tam (A yeni değeri, B eski değeri görüyor).")
    elif kirli:
        mesajlar.append("g2_kirli.txt eksik: transkriptte hem A'nın gördüğü yeni "
                        "değer hem B'nin gördüğü eski değer bulunmalı.")
    else:
        mesajlar.append("sonuc/g2_kirli.txt bulunamadı.")

    tekrar = oku("sonuc/g2_tekrar.txt") or ""
    eski, yeni = kredi[7], kredi[7] + TEKRAR_ARTIS
    if tekrar and re.search(r"REPEATABLE\s+READ", tekrar, re.IGNORECASE) \
            and sayi_var(tekrar, eski) and sayi_var(tekrar, yeni):
        puan += 13
        mesajlar.append("Tekrarlanabilir okuma deneyi kanıtı tam.")
    elif tekrar:
        mesajlar.append("g2_tekrar.txt eksik: REPEATABLE READ ve iki okuma "
                        "değeri (eski/yeni) transkriptte görünmeli.")
    else:
        mesajlar.append("sonuc/g2_tekrar.txt bulunamadı.")

    kaydet("Görev 2 (Isolation)", puan, 25, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 3
def kontrol_g3(kredi):
    icerik = oku("sonuc/g3.txt") or ""
    puan = 0
    mesajlar = []
    kayip = kredi[5] + KAYIP_ARTIS            # kayıp güncelleme: +10 bir kez
    # Düzeltilmiş tur ya kaldığı yerden (K+10 → K+30) ya da şema sıfırlanıp
    # baştan (K → K+20) yapılmış olabilir; ikisi de geçerli.
    dogrular = (kredi[5] + 3 * KAYIP_ARTIS, kredi[5] + 2 * KAYIP_ARTIS)
    if not icerik:
        kaydet("Görev 3 (Kayıp Güncelleme)", 0, 25, "sonuc/g3.txt bulunamadı.")
        return
    if sayi_var(icerik, kayip) and any(sayi_var(icerik, d) for d in dogrular):
        puan += 15
        mesajlar.append("Kayıp güncelleme ve düzeltilmiş sonuç değerleri yerinde.")
    else:
        mesajlar.append("Transkriptte hem kayıp güncelleme sonucu hem düzeltme "
                        "sonrası doğru bakiye görünmeli.")
    if re.search(r"FOR\s+UPDATE", icerik, re.IGNORECASE) or \
       re.search(r"kredi\s*=\s*kredi\s*\+", icerik, re.IGNORECASE):
        puan += 10
        mesajlar.append("Düzeltme tekniği (FOR UPDATE ya da atomik UPDATE) belgelenmiş.")
    else:
        mesajlar.append("Düzeltme tekniği transkriptte görünmüyor.")
    kaydet("Görev 3 (Kayıp Güncelleme)", puan, 25, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 4
def kontrol_g4(kredi):
    icerik = oku("sonuc/g4.txt") or ""
    puan = 0
    mesajlar = []
    if not icerik:
        kaydet("Görev 4 (Durability)", 0, 15, "sonuc/g4.txt bulunamadı.")
        return
    if sayi_var(icerik, kredi[9] + DAYANIKLILIK_ARTIS):
        puan += 10
        mesajlar.append("Yeniden başlatma sonrası bakiye kanıtı yerinde.")
    else:
        mesajlar.append("Restart sonrası SELECT çıktısında beklenen bakiye görünmüyor.")
    if "shared_buffers" in icerik:
        puan += 5
        mesajlar.append("Mimari gözlem (shared_buffers) yerinde.")
    else:
        mesajlar.append("SHOW shared_buffers çıktısı eksik.")
    kaydet("Görev 4 (Durability)", puan, 15, " ".join(mesajlar))


def ogrenci_metni(markdown):
    """Markdown'dan kod bloklarini atip ogrencinin KENDI yazdigi metni birakir.

    Yapay zekanin urettigi SQL'i yapistirip tek satir elestiri yazmayan
    teslimler yalnizca uzunluga bakildiginda esigi gecip tam puan aliyordu
    (gercek teslimlerde tespit edildi). Puan artik duz metne gore verilir.
    """
    m = markdown or ""
    m = re.sub(r"```.*?```", " ", m, flags=re.S)
    m = re.sub(r"```.*", " ", m, flags=re.S)
    m = re.sub(r"^\s{4,}\S.*$", " ", m, flags=re.M)
    m = re.sub(r"`[^`]*`", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def kontrol_ai():
    icerik = oku("sonuc/ai_elestiri.md")
    if not icerik or len(ogrenci_metni(icerik)) < 300:
        kaydet("AI Köşesi", 0, 10,
               "sonuc/ai_elestiri.md yok ya da eleştiri metniniz 300 karakterden kısa "
               "(yapıştırdığınız kod blokları sayılmaz). Föyde istenen iki "
               "somut eleştiriyi yazdığınızda bu uzunluk zaten aşılır "
               "(içerik ayrıca asistan tarafından okunur).")
    else:
        kaydet("AI Köşesi", 10, 10,
               "Dosya teslim edildi (isabet puanı asistan değerlendirmesiyle kesinleşir).")


# ------------------------------------------------------------- ana akış
def main():
    print("=" * 64)
    print("Föy 05 — Otomatik Değerlendirme")
    print("=" * 64)

    ogrno = ogrno_al()
    if not ogrno:
        print("HATA: ogrno.txt bulunamadı ya da geçerli bir numara içermiyor.")
        sys.exit(1)
    print(f"Öğrenci no: {ogrno} (veri seti bu numaradan yeniden üretiliyor)\n")

    t = uret(ogrno)
    kredi = {k["uye_id"]: k["kredi"] for k in t["krediler"]}

    with baglanti() as con:
        sema_kur(con, t)
        kontrol_g1(con, kredi)
    kontrol_g2(kredi)
    kontrol_g3(kredi)
    kontrol_g4(kredi)
    kontrol_ai()

    alinan = sum(s[1] for s in SONUCLAR)
    tam = sum(s[2] for s in SONUCLAR)
    print("\n" + "=" * 64)
    print(f"TOPLAM (otomatik kontrol edilen kısım): {alinan}/{tam}")
    print("Transkriptlerin içeriği ve savunma asistan tarafından")
    print("ayrıca değerlendirilir.")
    print("=" * 64)

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write("## Föy 05 — Otomatik Değerlendirme\n\n")
            f.write("| Bileşen | Puan | Açıklama |\n|---|---|---|\n")
            for gorev, a, tp, m in SONUCLAR:
                f.write(f"| {gorev} | {a}/{tp} | {m} |\n")
            f.write(f"| **Toplam** | **{alinan}/{tam}** | |\n")

    sys.exit(0 if alinan == tam else 1)


if __name__ == "__main__":
    main()
