-- =====================================================
-- Föy 05 — Şema + kredi sisteminin kurulumu — HAZIR DOSYA
-- Bu dosyayı DEĞİŞTİRMEYİN; olduğu gibi çalıştırın:
--   docker exec -i vtys-postgres psql -U vtys -d vtysdb < sql/sema_hazir.sql
-- (Bilinen şemaya bu hafta "krediler" tablosu eklendi.)
-- =====================================================
DROP TABLE IF EXISTS kayitlar, telefonlar, dersler, salonlar,
                     egitmenler, uyeler CASCADE;

CREATE TABLE uyeler (
    uye_id     INTEGER PRIMARY KEY,
    ad         VARCHAR(100) NOT NULL,
    dogum_yili SMALLINT
);
CREATE TABLE telefonlar (
    telefon_id INTEGER PRIMARY KEY,
    uye_id     INTEGER NOT NULL REFERENCES uyeler(uye_id),
    numara     VARCHAR(20) NOT NULL
);
CREATE TABLE egitmenler (
    egitmen_id INTEGER PRIMARY KEY,
    ad         VARCHAR(100) NOT NULL,
    brans      VARCHAR(50)
);
CREATE TABLE salonlar (
    salon_id  INTEGER PRIMARY KEY,
    ad        VARCHAR(50) NOT NULL,
    kapasite  SMALLINT
);
CREATE TABLE dersler (
    ders_id    INTEGER PRIMARY KEY,
    ad         VARCHAR(100) NOT NULL,
    egitmen_id INTEGER NOT NULL REFERENCES egitmenler(egitmen_id),
    salon_id   INTEGER NOT NULL REFERENCES salonlar(salon_id),
    ucret      INTEGER
);
CREATE TABLE kayitlar (
    kayit_id INTEGER PRIMARY KEY,
    uye_id   INTEGER NOT NULL REFERENCES uyeler(uye_id),
    ders_id  INTEGER NOT NULL REFERENCES dersler(ders_id),
    tarih    DATE
);

COPY uyeler     FROM '/veri/uyeler.csv'     WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY telefonlar FROM '/veri/telefonlar.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY egitmenler FROM '/veri/egitmenler.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY salonlar   FROM '/veri/salonlar.csv'   WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY dersler    FROM '/veri/dersler.csv'    WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY kayitlar   FROM '/veri/kayitlar.csv'   WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

DROP TABLE IF EXISTS krediler CASCADE;
CREATE TABLE krediler (
    uye_id INTEGER PRIMARY KEY REFERENCES uyeler(uye_id),
    kredi  INTEGER NOT NULL CHECK (kredi >= 0)
);
COPY krediler FROM '/veri/krediler.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
