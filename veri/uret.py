#!/usr/bin/env python3
"""Kişiye özel veri üreteci — Föy 05 (FıratFit + kredi sistemi)

Kullanım:
    python3 veri/uret.py <ogrenci_no>

Yedi CSV üretir: uyeler, telefonlar, egitmenler, salonlar, dersler,
kayitlar ve krediler. FıratFit bu hafta ön ödemeli 'ders kredisi' sistemine
geçti: her üyenin bir kredi bakiyesi var. ACID deneylerini bu bakiyeler
üzerinde yapacaksınız. Aynı numara her zaman aynı veriyi üretir.
"""
import csv
import random
import sys
from pathlib import Path

ADLAR = ["Ahmet", "Ayşe", "Mehmet", "Elif", "Mustafa", "Zeynep", "Ali",
         "Fatma", "Hasan", "Emine", "Murat", "Hülya", "Kemal", "Nazlı",
         "Selim", "Leyla", "Orhan", "Sevgi", "Yakup", "Melek", "Deniz",
         "Ece", "Burak", "Ceren", "Tolga", "İpek", "Serkan", "Gül"]

SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Aydın",
            "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç", "Kurt",
            "Özdemir", "Erdoğan", "Polat", "Güneş", "Taş", "Bulut"]

BRANSLAR = ["Fitness", "Yoga", "Pilates", "Yüzme", "Boks", "Crossfit"]

DERS_TEMEL = ["Sabah Yogası", "Fonksiyonel Antrenman", "Yüzme Teknikleri",
              "Pilates Matwork", "Boks Temelleri", "Crossfit WOD",
              "Core Güçlendirme", "Esneklik ve Denge", "Kardiyo Dayanıklılık",
              "Kuvvet Antrenmanı", "Hamile Yogası", "Kıdemli Fitness",
              "Gençlik Yüzme", "İleri Pilates", "Kickboks"]

SEVIYELER = ["Başlangıç", "Orta", "İleri"]

SALON_ADLARI = ["Ana Salon", "Stüdyo A", "Stüdyo B", "Havuz",
                "Dövüş Salonu", "Açık Alan", "Spinning Odası"]

UCRETLER = [300, 350, 400, 450, 500, 550, 600]


def uret(ogrno: str):
    """Öğrenci numarasından deterministik altı tablo üretir."""
    tohum = int(ogrno)
    rnd = random.Random(tohum)

    # --- salonlar (5–7) ---
    salon_sayisi = 5 + tohum % 3
    salonlar = [{"salon_id": i + 1, "ad": SALON_ADLARI[i],
                 "kapasite": rnd.choice([15, 20, 25, 30, 40])}
                for i in range(salon_sayisi)]

    # --- eğitmenler (8–12); ilk 6'sı altı branşı garanti kapsar ---
    egitmen_sayisi = 8 + tohum % 5
    branslar = BRANSLAR[:]
    rnd.shuffle(branslar)
    egitmen_adlari = set()
    egitmenler = []
    for eid in range(1, egitmen_sayisi + 1):
        while True:
            ad = f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}"
            if ad not in egitmen_adlari:
                egitmen_adlari.add(ad)
                break
        brans = branslar[eid - 1] if eid <= 6 else rnd.choice(BRANSLAR)
        egitmenler.append({"egitmen_id": eid, "ad": ad, "brans": brans})

    # --- dersler (24–32) ---
    ders_sayisi = 24 + tohum % 9
    ders_adlari = set()
    dersler = []
    for did in range(1, ders_sayisi + 1):
        while True:
            ad = f"{rnd.choice(DERS_TEMEL)} — {rnd.choice(SEVIYELER)}"
            if ad not in ders_adlari:
                ders_adlari.add(ad)
                break
        dersler.append({
            "ders_id": did,
            "ad": ad,
            "egitmen_id": rnd.randint(1, egitmen_sayisi),
            "salon_id": rnd.randint(1, salon_sayisi),
            "ucret": rnd.choice(UCRETLER),
        })

    # --- üyeler (150–200) ve telefonları ---
    uye_sayisi = 150 + tohum % 51
    uyeler = []
    telefonlar = []
    tel_id = 0
    for uid in range(1, uye_sayisi + 1):
        uyeler.append({
            "uye_id": uid,
            "ad": f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}",
            "dogum_yili": rnd.randint(1965, 2008),
        })
        for _ in range(rnd.randint(1, 3)):
            tel_id += 1
            telefonlar.append({
                "telefon_id": tel_id,
                "uye_id": uid,
                "numara": f"05{rnd.randint(30, 55)}-{rnd.randint(100, 999)}-"
                          f"{rnd.randint(1000, 9999)}",
            })

    # --- kayıtlar (320–420) ---
    # * 3–6 üye bilerek hiç kaydolmaz (Soru 2.3 için garanti)
    # * ilk 12 kayıt 12 ayı garanti kapsar (Soru 4.3 için)
    kayitsiz_sayisi = 3 + tohum % 4
    kayitsizlar = set(rnd.sample(range(1, uye_sayisi + 1), kayitsiz_sayisi))
    kayit_uyeleri = [u for u in range(1, uye_sayisi + 1) if u not in kayitsizlar]

    kayit_hedefi = 320 + tohum % 101
    ikili_kume = set()
    kayitlar = []
    kid = 0
    while kid < kayit_hedefi:
        uye = rnd.choice(kayit_uyeleri)
        ders = rnd.randint(1, ders_sayisi)
        if (uye, ders) in ikili_kume:
            continue
        ikili_kume.add((uye, ders))
        kid += 1
        ay = kid if kid <= 12 else rnd.randint(1, 12)
        gun = rnd.randint(1, 28)
        kayitlar.append({
            "kayit_id": kid,
            "uye_id": uye,
            "ders_id": ders,
            "tarih": f"2026-{ay:02d}-{gun:02d}",
        })

    # --- krediler: her üyenin ön ödemeli ders kredisi bakiyesi ---
    krediler = [{"uye_id": u["uye_id"], "kredi": rnd.randint(100, 900)}
                for u in uyeler]

    return {"uyeler": uyeler, "telefonlar": telefonlar,
            "egitmenler": egitmenler, "salonlar": salonlar,
            "dersler": dersler, "kayitlar": kayitlar,
            "krediler": krediler}


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Kullanım: python3 veri/uret.py <ogrenci_no>")
        print("Örnek   : python3 veri/uret.py 230541001")
        sys.exit(1)

    ogrno = sys.argv[1]
    klasor = Path(__file__).resolve().parent
    tablolar = uret(ogrno)

    for ad, satirlar in tablolar.items():
        hedef = klasor / f"{ad}.csv"
        with open(hedef, "w", newline="", encoding="utf-8") as f:
            yazici = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
            yazici.writeheader()
            yazici.writerows(satirlar)
        print(f"Üretildi: {hedef.name:16s} ({len(satirlar)} satır)")

    print("Bu dosyalar size özeldir; sonuçlarınız sınıftaki herkesten farklıdır.")


if __name__ == "__main__":
    main()
