CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS wydzialy_uczelni (
    akronim VARCHAR(10) CONSTRAINT pk_wydzialy_uczelni PRIMARY KEY,
    nazwa VARCHAR(150) CONSTRAINT uk_nazwa UNIQUE
);

CREATE TABLE IF NOT EXISTS kierunki_studiow (
    id SERIAL CONSTRAINT pk_kierunki_studiow PRIMARY KEY,
    nazwa VARCHAR(50) NOT NULL,
    stopien INT NOT NULL CHECK (stopien IN (1, 2)), -- 1 - inżynierskie/licencjackie, 2 - magisterskie
    tryb VARCHAR(50) NOT NULL CHECK (tryb IN ('stacjonarne', 'niestacjonarne')),
    profil VARCHAR(50) NOT NULL DEFAULT 'ogólnoakademicki',
    wydzial VARCHAR(10) CONSTRAINT fk_wydzial REFERENCES wydzialy_uczelni(akronim),
    w_jezyku_angielskim BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uk_kierunek UNIQUE (nazwa, stopien, tryb)
);

CREATE TABLE IF NOT EXISTS progi_punktowe (
    id SERIAL CONSTRAINT pk_progi_punktowe PRIMARY KEY,
    id_kierunku INT NOT NULL CONSTRAINT fk_progi_punktowe REFERENCES kierunki_studiow(id) ON DELETE CASCADE,    rok INT NOT NULL,
    tura INT NOT NULL DEFAULT 1 CONSTRAINT ck_tura CHECK(tura BETWEEN 1 AND 2),
    min_l_pkt NUMERIC(5,2) NOT NULL,
    limit_przyjec INT NOT NULL,
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_progi_punktowe UNIQUE (id_kierunku, rok, tura)
);

CREATE TABLE IF NOT EXISTS przedmioty (
    id SERIAL PRIMARY KEY,
    id_kierunku INT NOT NULL CONSTRAINT fk_kierunki_studiow REFERENCES kierunki_studiow(id) ON DELETE CASCADE,
    semestr INT NOT NULL CHECK (semestr BETWEEN 1 AND 8),
    nazwa VARCHAR(200) NOT NULL,
    w_jezyku_angielskim BOOLEAN NOT NULL DEFAULT FALSE,
    ects INT NOT NULL CHECK (ects >= 0),
    godz_w INT NOT NULL DEFAULT 0, -- Wykład
    godz_c INT NOT NULL DEFAULT 0, -- Ćwiczenia
    godz_l INT NOT NULL DEFAULT 0, -- Laboratoria
    godz_p INT NOT NULL DEFAULT 0, -- Projekt
    forma_zal VARCHAR(50), -- np. Egzamin, Zaliczenie ocena
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_przedmioty UNIQUE (id_kierunku, semestr, nazwa)
);

CREATE TABLE IF NOT EXISTS pracownicy (
    id SERIAL PRIMARY KEY,
    imie VARCHAR(50) NOT NULL,
    nazwisko VARCHAR(50) NOT NULL,
    tytul_naukowy VARCHAR(100),
    jednostka VARCHAR(200), -- np. Instytut Informatyki, Zakład Systemów Komputerowych
    email VARCHAR(100),
    nr_telefonu VARCHAR(100),
    pokoj VARCHAR(100),
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS konsultacje (
    id SERIAL PRIMARY KEY,
    pracownik_id INT NOT NULL CONSTRAINT fk_pracownicy REFERENCES pracownicy(id) ON DELETE CASCADE,
    semestr VARCHAR(50) NOT NULL, -- np. "letni 2025/2026"
    dzien_tygodnia VARCHAR(20) NOT NULL,    -- np. "Poniedziałek"
    godz_od TIME NOT NULL,
    godz_do TIME NOT NULL,
    miejsce VARCHAR(100),         -- np. "pok. 104 BT", "MS Teams"
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_konsultacje UNIQUE (pracownik_id, semestr, dzien_tygodnia, godz_od)
    );


