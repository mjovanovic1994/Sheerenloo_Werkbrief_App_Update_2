from flask import Flask, render_template, redirect, url_for, session, request, flash, make_response
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired
import os
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime
import pdfkit
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import logging
import secrets
from wtforms.validators import Optional



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

app = Flask(__name__)
secret = os.environ.get("SECRET_KEY")

if not secret:
    raise RuntimeError("SECRET_KEY is missing (.env niet geladen of ontbreekt)")

app.config['SECRET_KEY'] = secret
    
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///app.db"
)


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
secrets.token_hex(32)

csrf = CSRFProtect(app)

class Werkbrief(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.String(50))
    meta = db.Column(db.JSON)
    items = db.Column(db.JSON)

logging.basicConfig(level=logging.INFO)

KOSTENPLAATSEN = [
    "20867", "20393", "23215", "20863", "20852",
    "20856", "20855", "23820", "20854", "23780",
    "20788", "20727", "22322", "20864", "20823",
    "21759", "20754", "5381", "20721", "23267",
    "20570", "20828", "23859", "22726", "49240",
    "20839", "20837", "23814", "90205", "10545"
]

PRIJSAANPASSING = {
    # (budgethouder, locatie, kostenplaats): multiplier
    # voorbeeld (later uitbreidbaar)
    ("Jenneke van Dam", "Proosdij", "20867"): 1.0,
}
# ---------------- PRIJZEN ----------------
PRIJZEN = {

# ---------------- ZWART/WIT A4 ----------------
("Print Zwart/Wit","A4","80","Enkelzijdig"): 0.06,
("Print Zwart/Wit","A4","80","Dubbelzijdig"): 0.09,
("Print Zwart/Wit","A4","120","Enkelzijdig"): 0.10,
("Print Zwart/Wit","A4","120","Dubbelzijdig"): 0.15,
("Print Zwart/Wit","A4","160","Enkelzijdig"): 0.15,
("Print Zwart/Wit","A4","160","Dubbelzijdig"): 0.18,
("Print Zwart/Wit","A4","200","Enkelzijdig"): 0.20,
("Print Zwart/Wit","A4","200","Dubbelzijdig"): 0.25, 
("Print Zwart/Wit","A4","250","Enkelzijdig"): 0.27,
("Print Zwart/Wit","A4","250","Dubbelzijdig"): 0.32,

# ---------------- ZWART/WIT A3 ----------------
("Print Zwart/Wit","A3","80","Enkelzijdig"): 0.10,
("Print Zwart/Wit","A3","80","Dubbelzijdig"): 0.16,
("Print Zwart/Wit","A3","120","Enkelzijdig"): 0.20,
("Print Zwart/Wit","A3","120","Dubbelzijdig"): 0.30,
("Print Zwart/Wit","A3","200","Enkelzijdig"): 0.33,
("Print Zwart/Wit","A3","200","Dubbelzijdig"): 0.45,

# ---------------- ZWART/WIT SRA3 ----------------
("Print Zwart/Wit","SRA3","120","Enkelzijdig"): 0.22,
("Print Zwart/Wit","SRA3","120","Dubbelzijdig"): 0.35,
("Print Zwart/Wit","SRA3","200","Enkelzijdig"): 0.33,
("Print Zwart/Wit","SRA3","200","Dubbelzijdig"): 0.45,
("Print Zwart/Wit","SRA3","300","Enkelzijdig"): 0.40,
("Print Zwart/Wit","SRA3","300","Dubbelzijdig"): 0.55,

# ---------------- KLEUR A4 ----------------
("Print Kleur","A4","80","Enkelzijdig"): 0.23,
("Print Kleur","A4","80","Dubbelzijdig"): 0.33,
("Print Kleur","A4","120","Enkelzijdig"): 0.25,
("Print Kleur","A4","120","Dubbelzijdig"): 0.35,
("Print Kleur","A4","160","Enkelzijdig"): 0.27,
("Print Kleur","A4","160","Dubbelzijdig"): 0.40,
("Print Kleur","A4","200","Enkelzijdig"): 0.31,
("Print Kleur","A4","200","Dubbelzijdig"): 0.45,
("Print Kleur","A4","250","Enkelzijdig"): 0.37,
("Print Kleur","A4","250","Dubbelzijdig"): 0.48,
("Print Kleur","A4","300","Enkelzijdig"): 0.40,
("Print Kleur","A4","300","Dubbelzijdig"): 0.52,

# ---------------- KLEUR A3 ----------------
("Print Kleur","A3","80","Enkelzijdig"): 0.40,
("Print Kleur","A3","80","Dubbelzijdig"): 0.55,
("Print Kleur","A3","120","Enkelzijdig"): 0.64,
("Print Kleur","A3","120","Dubbelzijdig"): 0.78,
("Print Kleur","A3","200","Enkelzijdig"): 0.72,
("Print Kleur","A3","200","Dubbelzijdig"): 0.90,

# ---------------- KLEUR SRA3 ----------------
("Print Kleur","SRA3","80","Enkelzijdig"): 0.44,
("Print Kleur","SRA3","80","Dubbelzijdig"): 0.95,
("Print Kleur","SRA3","120","Enkelzijdig"): 1.20,
("Print Kleur","SRA3","120","Dubbelzijdig"): 1.55,
("Print Kleur","SRA3","200","Enkelzijdig"): 1.29,
("Print Kleur","SRA3","200","Dubbelzijdig"): 2.00,

# ---------------- KRAFTPAPIER ----------------
("Kraftpapier","","300","Enkelzijdig"): 0.45,
("Kraftpapier","","300","Dubbelzijdig"): 0.52,

# ---------------- LAMINEREN ----------------
("Lamineren","A5","300",""): 1.00,
("Lamineren","A4","300",""): 1.50,
("Lamineren","A3","300",""): 2.50,

# ---------------- HANDELINGEN ----------------
("Bewerking","Etiketten plakken","",""): 0.01,
("Bewerking","Enveloppen sluiten","",""): 0.01,
("Bewerking","Postzegels plakken","",""): 0.01,
("Bewerking","Rapen","",""): 0.02,
("Bewerking","Vouwen","",""): 0.01,
("Bewerking","Vouwen boekje","",""): 0.02,
("Bewerking","Nieten","",""): 0.01,
("Bewerking","Snijden","",""): 0.01,
("Bewerking","Perforeren","",""): 0.01,
("Bewerking","Rillen","",""): 0.01,

# ---------------- EXTRA KOSTEN ----------------
("Extra","Excel/Word etiketten","",""): 5.00,
("Extra","Klaarzetten ontwerp","",""): 2.50,
("Extra","Bestanden overzetten","",""): 5.00,
("Extra","Starttarief","",""): 1.00,
("Extra","Ontwerp","",""): 25.00,

# ---------------- VASTE KOSTEN ----------------
("Vaste Kosten","Uitstroom medewerkers","",""): 0.50,
("Vaste Kosten","Vrijwilligers kaarten","",""): 1.81,
("Vaste Kosten","Hartennieuws","",""): 1.82,
("Vaste Kosten","Online uitnodigingen","",""): 25.00,
("Vaste Kosten","Etiketten zonder papier","",""): 0.05,
("Vaste Kosten","Poster A3 kleur gelamineerd","",""): 1.90,

# ---------------- INBINDEN ----------------
("Inbinden","10mm","",""): 1.00,
("Inbinden","14mm","",""): 1.50,
("Inbinden","Transparant vel","",""): 0.10,

# ---------------- ETIKETTEN ----------------
("Etiketten","8 per vel","",""): 0.45,
("Etiketten","24 per vel","",""): 0.87,

# ---------------- VISITEKAARTJES ----------------
("Visitekaartjes","250g stuk","",""): 0.09,
("Visitekaartjes","50 stuks","",""): 3.50,
("Visitekaartjes","100 stuks","",""): 6.40,
("Visitekaartjes","A5 160g","",""): 0.30,
("Visitekaartjes","A5 gevouwen","",""): 1.00,
("Visitekaartjes","A5 open","",""): 1.50,
("Visitekaartjes","A6 intern","",""): 0.30,
("Visitekaartjes","Nieuwe medewerker","",""): 1.25,
("Visitekaartjes","Kerstkaart","",""): 1.50,
("Visitekaartjes","Bloemen kaartje","",""): 0.05,

# ---------------- FLYERS ----------------
("Flyers","A4","250","Enkelzijdig 1-200"): 0.20,
("Flyers","A4","250","Dubbelzijdig 1-200"): 0.40,
("Flyers","A5","250","Enkelzijdig 1-200"): 0.12,
("Flyers","A5","250","Dubbelzijdig 1-200"): 0.25,

# ---------------- GEKLEURD PAPIER ----------------
("Gekleurd papier","A4","120","Enkelzijdig"): 0.20,
("Gekleurd papier","A4","120","Dubbelzijdig"): 0.12,
("Gekleurd papier","A4","230","Enkelzijdig"): 0.14,
("Gekleurd papier","A4","230","Dubbelzijdig"): 0.16,

# ---------------- NOTITIEBOEKJE ----------------
("Notitieboekje","per 100","",""): 0.30,
("Notitieboekje","Kartonnen achterkant","",""): 0.10,
("Notitieboekje","Rondje uitsnijden","",""): 0.15,
("Notitieboekje","Kalender + oog","",""): 6.00,


# ---------------- ENVELOPPEN ----------------
("Enveloppen","A6","",""): 0.33,
("Enveloppen","Roma 100","",""): 0.29,

# ---------------- POSTSERVICE ----------------
("Postservice","Doosje vouwen","",""): 0.05,
("Postservice","Gadget erin","",""): 0.02,
("Postservice","Mailing","",""): 0.05,
("Postservice","Vouwen","",""): 0.02,
("Postservice","Extra flyer","",""): 0.01,
("Postservice","Postzegel","",""): 1.31,
("Postservice","Envelop A5","",""): 0.05,
}

PRODUCT_NAMEN = ["Print Zwart/Wit","Print Kleur","Lamineren","Etiketten plakken","Enveloppen sluiten"]

SUBCATEGORIEEN = {
    "Vaste Kosten": [
        "Uitstroom medewerkers",
        "Vrijwilligers kaarten",
        "Hartennieuws",
        "Online uitnodigingen",
        "Etiketten zonder papier",
        "Poster A3 kleur gelamineerd"
    ]
}

BUDGETHOUDER_LOCATIES = {
    "Jenneke van Dam": [
        "Proosdij", "Het Hart", "Buitendienst", "Bakkerij Smul", "Rotonde",
        "Makandra", "Voetbalwerkplaats", "Academie voor Zelfstandigheid",
        "Jobcoach", "Vrijwillige inzet", "Theehuis de Roek", "Recreatie",
        "Innovatie"
    ],
    "Marieke de Jong": [
        "Rietkampen", "DAC. Rietkampen", "Wasserij", "Buitenland (Parkboerderij)"
    ],
    "Ellen Smulders": [
        "Elsenhoek", "Molenweg 24"
    ],
    "Kristel van Ommeren": [
        "Bureau VOOR", "Eekhoornstraat 9", "Hagedisstraat 7-11"
    ],
    "Hester de Graaf": [
        "OR", "Duurzaamheid", "Communicatie", "Recruitment",
        "Secretariaat Management", "Gelderland Midden"
    ],
    "Wilma Fontaine": [
        "Wilma Fontaine", "Het Panorama"
    ],
    "Anneloes Welvering": [
        "Hagedisstraat 8"
    ],
    "Buitenland Gelderland Midden": [
        "Kasgroep"
    ],
    "Lucretia Visser": [
        "Visitekaartjes"
    ],
    "Mieke Kruizinga": [
        "Erasmusstate 81-83"
    ],
    "Corrie Ruttenberg": [
        "EMB", "Onder 1 Dak"
    ],
    "Judith Wagenmaker": [
        "Opleiding"
    ],
    "Elly Westerdijk": [
        "Academie"
    ]
}

BUDGETHOUDERS = {
    "Jenneke van Dam": [
        "20867", "20393", "23215", "20863", "20852",
        "20856", "20855", "23820", "20854", "23780",
        "20788", "20727", "22921"
    ],

    "Marieke de Jong": [
        "20869", "20783", "22322"
    ],

    "Ellen Smulders": [
        "20864", "20823"
    ],

    "Kristel van Ommeren": [
        "21759", "20754", "5381"
    ],

    "Hester de Graaf": [
        "23267", "20570"
    ],

    "Wilma Fontaine": [
        "20828", "23859"
    ],

    "Anneloes Welvering": [
        "22726"
    ],

    "Buitenland Gelderland Midden": [
        "23222"
    ],

    "Lucretia Visser": [
        "49240"
    ],

    "Mieke Kruizinga": [
        "20839"
    ],

    "Corrie Ruttenberg": [
        "20837", "23814"
    ],

    "Judith Wagenmaker": [
        "90205"
    ],

    "Elly Westerdijk": [
        "10545"
    ]
}
# ---------------- FUNCTIES ----------------

def save_werkbrief_db(data):
    enriched_items = enrich_items(
        data.get("items", []),
        data.get("meta", {})
    )

    wb = Werkbrief(
        datum=datetime.now().strftime("%Y-%m-%d %H:%M"),
        meta=data.get("meta", {}),
        items=enriched_items
    )

    db.session.add(wb)
    db.session.commit()

def geldige_keys(filters):
    return [
        k for k in PRIJZEN.keys()
        if all(
            (not f or k[i] == f)
            for i, f in enumerate(filters)
        )
    ]

def geldige_combinaties():
    return set(PRIJZEN.keys())

def get_valid_values(field, current_filters):
    values = set()

    for rule in PRIJZEN.keys():
        ok = True

        for k, v in current_filters.items():
            if k in rule and rule[k] != v:
                ok = False
                break

        if ok and field in rule:
            values.add(rule[field])

    return sorted(values)

def prijs_per_stuk(item, meta=None):
    naam = item.get("naam", "")
    formaat = item.get("formaat", "")
    gram = item.get("gram") or ""   # 👈 FIX
    zijde = item.get("zijde", "")
    sub = item.get("subcategorie", "")

    # 1. exacte match
    prijs = PRIJZEN.get((naam, formaat, gram, zijde))
    if prijs is not None:
        base = prijs
    else:
        # 2. fallback zonder gram
        prijs = PRIJZEN.get((naam, formaat, "", zijde))
        if prijs is not None:
            base = prijs
        else:
            # 3. subcategorie fallback
            prijs = PRIJZEN.get((naam, sub, "", ""))
            if prijs is not None:
                base = prijs
            else:
                base = 0.0

    multiplier = 1.0

    if base == 0:
        print("❌ NO PRICE MATCH:", naam, formaat, gram, zijde, sub)

    if meta:
        key = (
            meta.get("budgethouder"),
            meta.get("locatie"),
            meta.get("kostenplaats")
        )
        multiplier = PRIJSAANPASSING.get(key, 1.0)

    return base * multiplier

def totaal_prijs(items):
    return sum(prijs_per_stuk(i) * int(i.get('aantal',1)) for i in items)

def get_data():
    if "data" not in session:
        session["data"] = {"meta": {}, "items": []}
    return session["data"]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Je moet eerst inloggen.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def get_subcategorieen(categorie):
    return sorted(set(
        key[1] for key in PRIJZEN.keys()
        if key[0] == categorie and key[1]
    ))

def bereken_items(items, meta=None):
    enriched = enrich_items(items, meta)
    totaal = sum(i["prijs"] for i in enriched)
    return enriched, totaal

def validate(self):
    if not super().validate():
        return False

    # als print → gram verplicht
    if self.naam.data in ["Print Zwart/Wit", "Print Kleur"]:
        if not self.gram.data:
            self.gram.errors.append("Gram is verplicht voor print")
            return False

    return True

def enrich_items(items, meta=None):
    """Voegt prijs_per_stuk en totaal toe aan items"""
    resultaat = []

    for item in items:
        item_copy = dict(item)

        aantal = max(1, int(item_copy.get("aantal") or 1))
        prijs_stuk = prijs_per_stuk(item_copy, meta)
        totaal = prijs_stuk * aantal

        item_copy["aantal"] = aantal
        item_copy["prijs_per_stuk"] = prijs_stuk
        item_copy["prijs"] = totaal

        resultaat.append(item_copy)

    return resultaat

# ---------------- FORMS ----------------
class LoginForm(FlaskForm):
    username = StringField("Gebruikersnaam", validators=[DataRequired()])
    password = PasswordField("Wachtwoord", validators=[DataRequired()])
    submit = SubmitField("Inloggen")

class MetaForm(FlaskForm):
    naam_opdracht = StringField("Naam opdracht", validators=[DataRequired()])
    budgethouder = SelectField(
    "Budgethouder",
    choices=[("", "-- kies --")] + [
        (naam, naam) for naam in BUDGETHOUDERS.keys()
    ],
    validators=[Optional()]
)
    kostenplaatsen = SelectField(
    "Kostenplaats",
    choices=[],
    validators=[Optional()]
    )
    wat_opdracht = TextAreaField("Wat is de opdracht", validators=[DataRequired()])
    datum_binnenkomst = StringField("Datum binnenkomst")
    locatie = SelectField("Locatie", choices=[
        ("","--kies--"),
        ("Proosdij","Proosdij"),
        ("Het Hart", "Het Hart"),
        ("Buitendienst","Buitendienst"),
        ("Bakkerij Smul","Bakkerij Smul"),
        ("Rotonde","Rotonde"),
        ("Makandra","Makdandra"),
        ("Voetbalwerkplaats","Voetbalwerkplaats"),
        ("Academie voor Zelfstandigheid", "Academie voor Zelfstandigheid"),
        ("Jobcoach","Jobcoach"),
    ("Vrijwillige inzet", "Vrijwillige inzet"),
    ("Theehuis de Roek", "Theehuis de Roek"),
    ("Recreatie","Recreatie"),
    ("Innovatie","Innovatie"),
    ("Rietkampen","Rietkampen"),
    ("D.A.C. Rietkampen","D.A.C. Rietkampen"),
    ("Wasserij","Wasserij"),
    ("Buitenland (Parkboerderij)","Buitenland (Parkboerderij)"),
    ("Elsenhoek","Elsenhoek"),
    ("Molenweg 24","Molenweg 24"),
    ("Burea VOOR","Bureau VOOR"),
    ("Eekhoornstraat 9","Eekhoornstraat 9"),
    ("Hagedisstraat 7-11","Hagedisstraat 7-11"),
    ("OR","OR"),
    ("Duurzaamheid","Duurzaamheid"),
    ("Communicatie","Communicatie"),
    ("Recruitement","Recruitement"),
    ("Secretariaat Management","Secretariaat Management"),
    ("Gelderland Midden","Gelderland Midden"),
    ("Wilma Fontaine","Wilma Fontaine"),
    ("Het Panorama","Het Panorama"),
    ("Hagedisstraat 8","Hagedisstraat 8"),
    ("Kasgroep", "Kasgroep"),
    ("Visitekaartjes", "Visitekaartjes"),
    ("Erasmusstate 81-83","Erasmusstate 81-83"),
    ("EMB","EMB"),
    ("Onder 1 Dak","Onder 1 Dak"),
    ("Opleiding","Opleiding"),
    ("Academie","Academie")
    ],validators=[Optional()])
    deadline = StringField("Deadline")
    opdrachtnummer = StringField("Opdrachtnummer")
    telefoonnummer = StringField("Telefoonnummer")
    email = StringField("Email")
    contactpersoon = StringField("Contactpersoon")
    
    levering = SelectField("Levering", choices=[
        ("", "-- kies --"),
        ("Ophalen", "Ophalen"),
        ("Verzenden", "Verzenden"),
        ("Bezorgen", "Bezorgen")
    ])
    adres = StringField("Adres")

class ProductForm(FlaskForm):

    naam = SelectField("Categorie", choices=[
        ("", "-- kies --"),

        # Print
        ("Print Zwart/Wit", "Print Zwart/Wit"),
        ("Print Kleur", "Print Kleur"),

        # Overig
        ("Kraftpapier", "Kraftpapier"),
        ("Lamineren", "Lamineren"),

        # Extra / vaste kosten
        ("Extra", "Extra"),
        ("Vaste Kosten", "Vaste Kosten"),

        # Overige producten
        ("Inbinden", "Inbinden"),
        ("Etiketten", "Etiketten"),
        ("Visitekaartjes", "Visitekaartjes"),
        ("Flyers", "Flyers"),
        ("Gekleurd papier", "Gekleurd papier"),
        ("Notitieboekje", "Notitieboekje"),
        ("Enveloppen", "Enveloppen"),
        ("Postservice", "Postservice"),
    ])

    formaat = SelectField("Formaat", choices=[
        ("", "-- kies --"),
        ("A6","A6"),
        ("A5","A5"),
        ("A4","A4"),
        ("A3","A3"),
        ("SRA3","SRA3"),
    ])

    gram = SelectField("Gram", choices=[
        ("", "-- kies --"),
        ("80","80"),
        ("120","120"),
        ("160","160"),
        ("200","200"),
        ("230","230"),
        ("250","250"),
        ("300","300"),
    ])

    zijde = SelectField("Zijde", choices=[
        ("", "-- kies --"),
        ("Enkelzijdig","Enkelzijdig"),
        ("Dubbelzijdig","Dubbelzijdig"),
    ])

    aantal = IntegerField("Aantal", default=1)

    # 👇 BELANGRIJK: dit vervangt jouw oude subcategorie
    subcategorie = SelectField("Specificatie", choices=[
        ("", "-- kies --"),

        # Bewerking
        ("Etiketten plakken","Etiketten plakken"),
        ("Enveloppen sluiten","Enveloppen sluiten"),
        ("Postzegels plakken","Postzegels plakken"),
        ("Rapen","Rapen"),
        ("Vouwen","Vouwen"),
        ("Vouwen boekje","Vouwen boekje"),
        ("Nieten","Nieten"),
        ("Snijden","Snijden"),
        ("Perforeren","Perforeren"),
        ("Rillen","Rillen"),

        # Extra
        ("Excel/Word etiketten","Excel/Word etiketten"),
        ("Klaarzetten ontwerp","Klaarzetten ontwerp"),
        ("Bestanden overzetten","Bestanden overzetten"),
        ("Starttarief","Starttarief"),
        ("Ontwerp","Ontwerp"),

        # Inbinden
        ("10mm","10mm"),
        ("14mm","14mm"),
        ("Transparant vel","Transparant vel"),

        # Etiketten
        ("8 per vel","8 per vel"),
        ("24 per vel","24 per vel"),

        # Visitekaartjes
        ("250g stuk","250g stuk"),
        ("50 stuks","50 stuks"),
        ("100 stuks","100 stuks"),
        ("A5 160g","A5 160g"),
        ("A5 gevouwen","A5 gevouwen"),
        ("A5 open","A5 open"),
        ("A6 intern","A6 intern"),
        ("Nieuwe medewerker","Nieuwe medewerker"),
        ("Kerstkaart","Kerstkaart"),
        ("Bloemen kaartje","Bloemen kaartje"),

        # Flyers
        ("Enkelzijdig 1-200","Enkelzijdig 1-200"),
        ("Dubbelzijdig 1-200","Dubbelzijdig 1-200"),

        # Notitieboekje
        ("per 100","per 100"),
        ("Kartonnen achterkant","Kartonnen achterkant"),
        ("Rondje uitsnijden","Rondje uitsnijden"),
        ("Kalender + oog","Kalender + oog"),

        # Enveloppen
        ("A6","A6"),
        ("Roma 100","Roma 100"),

        # Postservice
        ("Doosje vouwen","Doosje vouwen"),
        ("Gadget erin","Gadget erin"),
        ("Mailing","Mailing"),
        ("Extra flyer","Extra flyer"),
        ("Postzegel","Postzegel"),
        ("Envelop A5","Envelop A5")
    
    
    ])
    bewerking = SelectField("Bewerking", choices=[
        ("", "--geen--"),
        ("Snijden", "Snijden"),
        ("Vouwen", "Vouwen"),
        ("Nieten", "Nieten"),
        ("Lamineren", "Lamineren"),
        ("Inbinden", "Inbinden"),
        ("Rapen", "Rapen"),
        ("Performeren", "Performeren"),
        ("Versturen", "Versturen"),
        ("Rillen", "Rillen")
    ])

    

class ProductListForm(FlaskForm):
    csrf_token = StringField()
    producten = FieldList(FormField(ProductForm), min_entries=1)

class DeleteForm(FlaskForm):
    submit = SubmitField("Verwijder")    

# ---------------- ROUTES ----------------

@app.route("/werkbrief/<int:wb_id>/delete", methods=["POST"])
@login_required
def delete_werkbrief(wb_id):
    wb = Werkbrief.query.get(wb_id)

    if not wb:
        flash("Werkbrief niet gevonden", "danger")
        return redirect(url_for("werkbrieven"))

    db.session.delete(wb)
    db.session.commit()

    flash("Werkbrief verwijderd", "success")
    return redirect(url_for("werkbrieven"))

@app.route("/werkbrief/<int:wb_id>/pdf")
@login_required
def werkbrief_pdf(wb_id):
    wb = Werkbrief.query.get(wb_id)

    if not wb:
        flash("Werkbrief niet gevonden", "danger")
        return redirect(url_for("werkbrieven"))

    items_met_prijs, totaal = bereken_items(wb.items, wb.meta)

    print(wb.items[0])

    rendered = render_template(
        "werkbrief.html",
        meta=wb.meta,
        items=items_met_prijs,
        totaal_prijs=totaal
    )

    try:
        pdf = pdfkit.from_string(rendered, False)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        return response
    except Exception:
        return rendered

@app.route("/werkbrieven")
@login_required
def werkbrieven():
    werkbrieven = Werkbrief.query.order_by(Werkbrief.id.desc()).all()
    form = DeleteForm()
    for wb in werkbrieven:
        wb.items, _ = bereken_items(wb.items, wb.meta)
        print(wb.items[0])
    return render_template("werkbrieven.html", werkbrieven=werkbrieven, form=form)

@app.route("/werkbrief/<int:wb_id>")
@login_required
def werkbrief_detail(wb_id):
    wb = Werkbrief.query.get(wb_id)

    if not wb:
        flash("Werkbrief niet gevonden", "danger")
        return redirect(url_for("werkbrieven"))

    items_met_prijs, totaal = bereken_items(wb.items, wb.meta)
    print(wb.items[0])

    return render_template(
        "werkbrief.html",
        meta=wb.meta,
        items=items_met_prijs,
        totaal_prijs=totaal
    )

USERS = {
    "admin": generate_password_hash("Sheerenloo_123!"),
    "gebruiker": generate_password_hash("Geheim_456!")
}

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        if form.username.data in USERS and check_password_hash(
            USERS[form.username.data],
            form.password.data
        ):
            session["logged_in"] = True
            session["username"] = form.username.data
            flash("Succesvol ingelogd!", "success")

            return redirect(url_for("meta"))

        # ❗ BELANGRIJK: ook bij fout altijd redirect (PRG pattern)
        flash("Ongeldige gebruikersnaam of wachtwoord.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash("Succesvol uitgelogd.", "success")
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
@login_required
def meta():

    data = get_data()
    form = MetaForm()
    meta = data.get("meta", {})

    # -------------------------
    # budgethouder bepalen
    # -------------------------
    gekozen_budgethouder = (
        form.budgethouder.data
        or request.form.get("budgethouder")
        or meta.get("budgethouder")
    )

    # -------------------------
    # kostenplaatsen (blijft zoals je had)
    # -------------------------
    kostenplaatsen = BUDGETHOUDERS.get(gekozen_budgethouder, [])

    form.kostenplaatsen.choices = [("", "-- kies --")] + [
        (k, k) for k in kostenplaatsen
    ]

    # -------------------------
    # 🔥 LOCATIES DYNAMISCH
    # -------------------------
    locaties = BUDGETHOUDER_LOCATIES.get(gekozen_budgethouder, [])

    form.locatie.choices = [("", "--kies--")] + [
        (l, l) for l in locaties
    ]

    # -------------------------
    # GET → vullen
    # -------------------------
    if request.method == "GET":
        form.process(data=meta)

    # -------------------------
    # POST → opslaan
    # -------------------------
    if request.method == "POST":

        if "opslaan" in request.form:

            if form.validate():

                data["meta"] = {
                    "naam_opdracht": form.naam_opdracht.data,
                    "budgethouder": form.budgethouder.data,
                    "kostenplaats": form.kostenplaatsen.data,
                    "wat_opdracht": form.wat_opdracht.data,
                    "datum_binnenkomst": form.datum_binnenkomst.data,
                    "deadline": form.deadline.data,
                    "locatie": form.locatie.data,
                    "opdrachtnummer": form.opdrachtnummer.data,
                    "telefoonnummer": form.telefoonnummer.data,
                    "email": form.email.data,
                    "contactpersoon": form.contactpersoon.data,
                    "levering": form.levering.data,
                    "adres": form.adres.data
                }

                session.modified = True
                return redirect(url_for("producten"))

        flash("Controleer de invoer.", "warning")

    return render_template("meta.html", form=form)

@app.route("/producten", methods=["GET", "POST"])
@login_required
def producten():
    data = get_data()

    if "items" not in data or not data["items"]:
        data["items"] = [{
            "naam": "",
            "formaat": "",
            "gram": "",
            "zijde": "",
            "aantal": 1,
            "subcategorie": "",
            "bewerking": ""
        }]

    items = data["items"]

    if request.method == "POST":

        if "add_product" in request.form:
            items.append({
                "naam": "",
                "formaat": "",
                "gram": "",
                "zijde": "",
                "aantal": 1,
                "subcategorie": "",
                "bewerking": ""
            })
            session.modified = True
            return redirect(url_for("producten"))

        elif "remove_product" in request.form:
            idx = int(request.form["remove_product"])
            if 0 <= idx < len(items):
                items.pop(idx)
                session.modified = True
            return redirect(url_for("producten"))

        elif "save" in request.form:

            nieuwe_items = []
            for p in ProductListForm(request.form).producten.entries:
                nieuwe_items.append({
                    "naam": p.form.naam.data,
                    "formaat": p.form.formaat.data,
                    "gram": p.form.gram.data,
                    "zijde": p.form.zijde.data,
                    "aantal": max(1, int(p.form.aantal.data or 1)),
                    "subcategorie": p.form.subcategorie.data,
                    "bewerking": p.form.bewerking.data
                })

            data["items"] = nieuwe_items
            session.modified = True

            enriched_items = enrich_items(nieuwe_items, data.get("meta", {}))

            wb = Werkbrief(
                datum=datetime.now().strftime("%Y-%m-%d %H:%M"),
                meta=data.get("meta", {}),
                items=enriched_items
            )

            db.session.add(wb)
            db.session.commit()

            return redirect(url_for("werkbrieven"))

    form = ProductListForm()
    form.producten.entries = []

    for item in items:
        form.producten.append_entry(item)

    return render_template("producten.html", form=form)

@app.route("/werkbrief")
@login_required
def werkbrief():
    data = get_data()

    items = data.get("items", [])

    items_met_prijs, totaal = bereken_items(items)

    meta_clean = {k: v for k, v in data.get("meta", {}).items() if k != "csrf_token"}

    return render_template(
        "werkbrief.html",
        meta=meta_clean,
        items=items_met_prijs,
        totaal_prijs=totaal
    )

@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



if __name__ == "__main__":
     app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

  
