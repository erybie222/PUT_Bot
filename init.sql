-- Turn on pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Testowa tabela kierunków studiów
CREATE TABLE IF NOT EXISTS studia_kierunki (
    id SERIAL PRIMARY KEY,
    nazwa VARCHAR(50) NOT NULL,
    stopien INT NOT NULL CHECK (stopien IN (1, 2)), -- 1 - inżynierskie/licencjackie, 2 - magisterskie
    tryb VARCHAR(50) NOT NULL CHECK (tryb IN ('stacjonarne', 'niestacjonarne')),
    profil VARCHAR(100) DEFAULT 'ogólnoakademicki',
    wydzial VARCHAR(50) DEFAULT 'WIiT',
    CONSTRAINT unique_kierunek UNIQUE (nazwa, stopien, tryb)
);
