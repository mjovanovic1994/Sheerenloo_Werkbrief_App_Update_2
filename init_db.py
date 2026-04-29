import sqlite3

conn = sqlite3.connect("prijzen.db")
cur = conn.cursor()

# ---------------- PRINT PRIJZEN ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS print_prijzen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_print TEXT,
    formaat TEXT,
    gram TEXT,
    zijde TEXT,
    prijs REAL,
    UNIQUE(type_print, formaat, gram, zijde)
)
""")

print_data = [
    # Zwart/Wit A4
    ("Zwart/Wit","A4","80","Enkelzijdig",0.06),
    ("Zwart/Wit","A4","80","Dubbelzijdig",0.09),
    ("Zwart/Wit","A4","120","Enkelzijdig",0.10),
    ("Zwart/Wit","A4","120","Dubbelzijdig",0.15),
    ("Zwart/Wit","A4","160","Enkelzijdig",0.15),
    ("Zwart/Wit","A4","160","Dubbelzijdig",0.18),
    ("Zwart/Wit","A4","200","Enkelzijdig",0.20),
    ("Zwart/Wit","A4","200","Dubbelzijdig",0.25),
    ("Zwart/Wit","A4","250","Enkelzijdig",0.27),
    ("Zwart/Wit","A4","250","Dubbelzijdig",0.32),
    # Zwart/Wit A3
    ("Zwart/Wit","A3","80","Enkelzijdig",0.10),
    ("Zwart/Wit","A3","80","Dubbelzijdig",0.16),
    ("Zwart/Wit","A3","120","Enkelzijdig",0.20),
    ("Zwart/Wit","A3","120","Dubbelzijdig",0.30),
    ("Zwart/Wit","A3","200","Enkelzijdig",0.33),
    ("Zwart/Wit","A3","200","Dubbelzijdig",0.45),
    # Zwart/Wit SRA3
    ("Zwart/Wit","SRA3","120","Enkelzijdig",0.22),
    ("Zwart/Wit","SRA3","120","Dubbelzijdig",0.35),
    ("Zwart/Wit","SRA3","200","Enkelzijdig",0.33),
    ("Zwart/Wit","SRA3","200","Dubbelzijdig",0.45),
    ("Zwart/Wit","SRA3","300","Enkelzijdig",0.40),
    ("Zwart/Wit","SRA3","300","Dubbelzijdig",0.55),
    # Kleur A4
    ("Kleur","A4","80","Enkelzijdig",0.23),
    ("Kleur","A4","80","Dubbelzijdig",0.33),
    ("Kleur","A4","120","Enkelzijdig",0.25),
    ("Kleur","A4","120","Dubbelzijdig",0.35),
    ("Kleur","A4","160","Enkelzijdig",0.27),
    ("Kleur","A4","160","Dubbelzijdig",0.40),
    ("Kleur","A4","200","Enkelzijdig",0.31),
    ("Kleur","A4","200","Dubbelzijdig",0.45),
    ("Kleur","A4","250","Enkelzijdig",0.37),
    ("Kleur","A4","250","Dubbelzijdig",0.48),
    ("Kleur","A4","300","Enkelzijdig",0.40),
    ("Kleur","A4","300","Dubbelzijdig",0.52),
    # Kleur A3
    ("Kleur","A3","80","Enkelzijdig",0.40),
    ("Kleur","A3","80","Dubbelzijdig",0.55),
    ("Kleur","A3","120","Enkelzijdig",0.64),
    ("Kleur","A3","120","Dubbelzijdig",0.78),
    ("Kleur","A3","200","Enkelzijdig",0.72),
    ("Kleur","A3","200","Dubbelzijdig",0.90),
    # Kleur SRA3
    ("Kleur","SRA3","80","Enkelzijdig",0.44),
    ("Kleur","SRA3","80","Dubbelzijdig",0.95),
    ("Kleur","SRA3","120","Enkelzijdig",1.20),
    ("Kleur","SRA3","120","Dubbelzijdig",1.55),
    ("Kleur","SRA3","200","Enkelzijdig",1.29),
    ("Kleur","SRA3","200","Dubbelzijdig",2.00),
    # Kraftpapier
    ("Kraftpapier","A4","300","Enkelzijdig",0.45),
    ("Kraftpapier","A4","300","Dubbelzijdig",0.52),
]

cur.executemany("INSERT OR IGNORE INTO print_prijzen (type_print, formaat, gram, zijde, prijs) VALUES (?,?,?,?,?)", print_data)

# ---------------- LAMINEREN ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS formaat_prijzen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_print TEXT,
    formaat TEXT,
    prijs REAL
)
""")

cur.executemany("INSERT OR IGNORE INTO formaat_prijzen (type_print, formaat, prijs) VALUES (?,?,?)", [
    ("Lamineren","A5",1.00),
    ("Lamineren","A4",1.50),
    ("Lamineren","A3",2.50),
])

# ---------------- HANDLINGEN / VASTE KOSTEN ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS acties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    prijs REAL
)
""")

acties_data = [
    # Handelingen
    ("etiketten plakken",0.01),
    ("enveloppen sluiten",0.01),
    ("overzetten Excel/Word voor etiketten",5.00),
    ("postzegels plakken",0.01),
    ("rapen",0.02),
    ("vouwen",0.01),
    ("vouwen per boekje",0.02),
    ("nieten per nietje",0.01),
    ("snijden per handeling machine",0.01),
    ("perforeren",0.01),
    ("klaarzetten in publisher/canva etc.",2.50),
    ("bestanden overzetten",5.00),
    ("starttarief",1.00),
    ("ontwerp",25.00),
    ("rillen 50 vellen",0.01),
    ("rillen instellen",0.02),

    # Vaste kosten
    ("uitstroom medewerkers per persoon",0.50),
    ("vrijwilligers verjaardagskaarten",1.81),
    ("hartennieuws per krant",1.82),
    ("online uitnodigingen",25.00),
    ("etiketten printen zonder papier",0.05),
    ("posters a3 kleur + lamineren per persoon",1.90),

    # Inbinden
    ("wire-o binden 10mm",1.00),
    ("wire-o binden 14mm",1.50),
    ("transparante bindomslag per vel",0.10),

    # Etiketten
    ("etiket stickers vellen 8 stuks per vel",0.45),
    ("etiket stickers vellen 24 stuks per vel",0.87),
]

cur.executemany("INSERT OR IGNORE INTO acties (naam, prijs) VALUES (?,?)", acties_data)

# ---------------- VISITEKAARTJES ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS producten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    formaat TEXT,
    prijs_per_stuk REAL,
    prijs_50 REAL,
    prijs_100 REAL
)
""")

producten_data = [
    ("250 gram 55x85mm","VK",0.09,3.50,6.40),
    ("160 gram A5","A5",0.30,None,None),
    ("A5 dubbelgevouwen tot A6","A5",1.00,None,None),
    ("A5 open","A5",1.50,None,None),
    ("A6 enkel binnen SHL","A6",0.30,None,None),
    ("nieuwe medewerkers inclusief postzegel","A6",1.25,None,None),
    ("kerstkaarten","A6",1.50,None,None),
    ("bloemen, kaarsen etc. ongeveer 5x7","A6",0.05,None,None),
]

cur.executemany("INSERT OR IGNORE INTO producten (naam, formaat, prijs_per_stuk, prijs_50, prijs_100) VALUES (?,?,?,?,?)", producten_data)

# ---------------- FLYERS ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS flyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formaat TEXT,
    oplage_range TEXT,
    prijs REAL
)
""")

flyers_data = [
    ("A4","001-200",0.20),
    ("A4","201-300",0.18),
    ("A4","301-500",0.15),
    ("A5","001-200",0.12),
    ("A5","201-300",0.11),
    ("A5","301-500",0.10),
]

cur.executemany("INSERT OR IGNORE INTO flyers (formaat, oplage_range, prijs) VALUES (?,?,?)", flyers_data)

# ---------------- NOTITIEBOEKJES ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS notitie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    prijs REAL
)
""")

notitie_data = [
    ("per 100",0.30),
    ("kartonnen achterkant",0.10),
    ("stukje rondje eruit halen",0.15),
    ("kalender + ophangoog per stuk",6.00),
]

cur.executemany("INSERT OR IGNORE INTO notitie (naam, prijs) VALUES (?,?)", notitie_data)

# ---------------- COMMUNICATIE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS communicatie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    prijs REAL
)
""")

communicatie_data = [
    ("300 gram kleur dubbelzijdig A6",0.24),
]

cur.executemany("INSERT OR IGNORE INTO communicatie (naam, prijs) VALUES (?,?)", communicatie_data)

# ---------------- ENVELOP & POSTSERVICE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS enveloppen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    prijs REAL
)
""")

enveloppen_data = [
    ("a6 wit per stuk",0.33),
    ("Roma per 100",0.29),
]

cur.executemany("INSERT OR IGNORE INTO enveloppen (naam, prijs) VALUES (?,?)", enveloppen_data)

cur.execute("""
CREATE TABLE IF NOT EXISTS postservice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT,
    prijs REAL
)
""")

postservice_data = [
    ("doosje vouwen",0.05),
    ("gadget erin",0.02),
    ("mailing",0.05),
    ("vouwen",0.02),
    ("extra flyer prijs per klant",0.01),
    ("postzegels nr.1 per stuk",1.31),
    ("enveloppen A5 uit per stuk",0.05),
]

cur.executemany("INSERT OR IGNORE INTO postservice (naam, prijs) VALUES (?,?)", postservice_data)

conn.commit()
conn.close()

print("✅ Database volledig aangemaakt en gevuld met alle producten en prijzen!")