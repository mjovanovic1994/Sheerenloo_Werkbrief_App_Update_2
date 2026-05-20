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

STANDAARDTARIEF = 1.00

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
        "Bureau VOOR", "Eekhoornstraat 9", "Hagedisstraat 7-11","Nachtzorg"
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
    ],

    "Gerdy van Achterberg":[
        "Pastoraat"
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
        "21759", "20754", "5381", "20764"
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
    ],

    "Gerdy van Achterberg":[
        "15408"
    ]
}

LOCATIE_KOSTENPLAATS = {
    "Proosdij": "20867",
    "Het Hart": "20393",
    "Buitendienst": "23215",
    "Bakkerij Smul": "20863",
    "Rotonde": "20852",
    "Makandra": "20856",
    "Voetbalwerkplaats": "20855",
    "Academie voor Zelfstandigheid": "23820",
    "Jobcoach": "20854",
    "Vrijwillige inzet": "23780",
    "Theehuis de Roek": "20788",
    "Recreatie": "20727",

    "Rietkampen": "20869",
    "DAC. Rietkampen": "20783",
    "Wasserij": "22322",

    "Elsenhoek": "20864",
    "Molenweg 24": "20823",

    "Bureau VOOR": "21759",
    "Eekhoornstraat 9": "20754",
    "Hagedisstraat 7-11": "5381",
    "Nachtzorg": "20764",

    "OR": "23267",
    "Duurzaamheid": "20570",

    "Het Panorama": "23859",

    "Hagedisstraat 8": "22726",

    "Kasgroep": "23222",

    "Visitekaartjes": "49240",

    "Erasmusstate 81-83": "20839",

    "EMB": "20837",
    "Onder 1 Dak": "23814",

    "Opleiding": "90205",

    "Academie": "10545",

    "Pastoraat": "15408",

}
# ---------------- FUNCTIES --------------

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

def build_price_keys(item):
    """
    Genereert fallback keys van specifiek → generiek
    """
    naam = norm(item.get("naam"))
    formaat = norm(item.get("formaat"))
    gram = norm(item.get("gram"))
    zijde = norm(item.get("zijde"))
    sub = norm(item.get("subcategorie"))

    keys = []

    # meest specifiek
    keys.append((naam, formaat, gram, zijde))
    keys.append((naam, formaat, "", zijde))
    keys.append((naam, formaat, "", ""))

    # subcategorie fallback (voor o.a. Bewerking / Inbinden / Extra)
    if sub:
        keys.append((naam, sub, "", ""))
        keys.append((sub, "", "", ""))

    # laatste fallback
    keys.append((naam, "", "", ""))

    return keys


def prijs_per_stuk(item, meta=None):

    naam = norm(item.get("naam"))
    sub = norm(item.get("subcategorie"))
    formaat = norm(item.get("formaat"))
    gram = norm(item.get("gram"))
    zijde = norm(item.get("zijde"))

    # =========================
    # ETIKETTEN SPECIAL CASE
    # =========================
    if naam == "Etiketten":

        if sub == "24 per vel":
            base = PRIJZEN.get(("Etiketten", "24 per vel", "", ""), 0)

        elif sub == "8 per vel":
            base = PRIJZEN.get(("Etiketten", "8 per vel", "", ""), 0)

        else:
            base = 0

        multiplier = 1.0

        if meta:
            multiplier = PRIJSAANPASSING.get(
                (
                    meta.get("budgethouder"),
                    meta.get("locatie"),
                    meta.get("kostenplaats")
                ),
                1.0
            )

        return round(base * multiplier, 2)

    # =========================
    # GENERIEKE PRIJZEN
    # =========================
    for key, price in PRIJZEN.items():

        match = True

        for i, val in enumerate(key):
            if val and val != [
                naam, formaat, gram, zijde
            ][i]:
                match = False
                break

        if match:
            return price

    # =========================
    # FALLBACK (BELANGRIJK!)
    # =========================
    return 0.0

def totaal_prijs(items):
    totaal_items = sum(
        prijs_per_stuk(i) * int(i.get('aantal', 1))
        for i in items
    )

    return round(totaal_items + STANDAARDTARIEF, 2)

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
    totaal = round(totaal + STANDAARDTARIEF, 2)

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
    resultaat = []

    for item in items:
        item = dict(item)

        aantal = int(item.get("aantal") or 1)
        if aantal < 1:
            aantal = 1

        prijs_stuk = round(prijs_per_stuk(item, meta), 2)
        totaal = round(prijs_stuk * aantal, 2)

        item.update({
            "aantal": aantal,
            "prijs_per_stuk": prijs_stuk,
            "prijs": totaal
        })

        resultaat.append(item)

    return resultaat 

def norm(value):
    if value is None:
        return ""
    return str(value).strip()

def build_price_key(item):
    naam = norm(item.get("naam"))
    sub = norm(item.get("subcategorie"))
    bewerking = norm(item.get("bewerking"))
    formaat = norm(item.get("formaat"))
    gram = norm(item.get("gram"))
    zijde = norm(item.get("zijde"))

    # Lamineren via bewerking ondersteunen
    if bewerking == "Lamineren":
        naam = "Lamineren"

    keys = [

        # Exacte match
        (naam, formaat, gram, zijde),

        # Zonder zijde
        (naam, formaat, gram, ""),

        # Subcategorie producten
        (naam, sub, "", ""),

        # Bewerkingen
        (naam, bewerking, "", ""),

        # Algemene fallback
        (naam, "", "", "")
    ]

    return keys

def get_kostenplaats_options(budgethouder, locatie):
    """
    Geeft lijst kostenplaatsen op basis van budgethouder + locatie
    """

    # 1. fallback: via LOCATIE_KOSTENPLAATS
    kp = LOCATIE_KOSTENPLAATS.get(locatie)

    if kp:
        return [kp]

    # 2. fallback: via BUDGETHOUDERS mapping
    return BUDGETHOUDERS.get(budgethouder, [])

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
    kostenplaats = SelectField(
        "Kostenplaats",
        choices=[],
        validators=[Optional()]
    )
    wat_opdracht = TextAreaField("Wat is de opdracht", validators=[DataRequired()])
    datum_binnenkomst = StringField("Datum binnenkomst")
   
    locatie = SelectField(
        "Locatie",
        choices=[],
        validators=[Optional()]
    )
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
        ("Envelop A5","Envelop A5"),
        ("Vrijwilligers kaarten","Vrijwilligers kaarten")
    
    
    ])
    bewerking = SelectField("Bewerking", choices=[
        ("", "--geen--"),
        ("Snijden", "Snijden"),
        ("Vouwen", "Vouwen"),
        ("Nieten", "Nieten"),
        ("Inbinden", "Inbinden"),
        ("Rapen", "Rapen"),
        ("Perforeren", "Perforeren"),
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
        wb.items, _ = bereken_items(wb.items, wb.meta or {})
    return render_template("werkbrieven.html", werkbrieven=werkbrieven, form=form)

@app.route("/werkbrief/<int:wb_id>")
@login_required
def werkbrief_detail(wb_id):
    wb = Werkbrief.query.get(wb_id)

    data = get_data()
    items = data.get("items", [])

    if not wb:
        flash("Werkbrief niet gevonden", "danger")
        return redirect(url_for("werkbrieven"))

    items_met_prijs, totaal = bereken_items(items, data.get("meta", {}))

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
    saved_meta = data.get("meta", {})

    form = MetaForm()

    # =========================
    # HUIDIGE DATA
    # =========================
    source = request.form if request.method == "POST" else saved_meta

    selected_locatie = source.get("locatie", "")

    # =========================
    # LOCATIES
    # =========================
    locaties = sorted(LOCATIE_KOSTENPLAATS.keys())

    form.locatie.choices = [
        ("", "-- kies --")
    ] + [
        (locatie, locatie)
        for locatie in locaties
    ]

    # =========================
    # KOSTENPLAATS AUTOMATISCH
    # =========================
    gekoppelde_kostenplaats = LOCATIE_KOSTENPLAATS.get(
        selected_locatie,
        ""
    )

    form.kostenplaats.choices = [
        ("", "-- kies --")
    ]

    if gekoppelde_kostenplaats:
        form.kostenplaats.choices.append(
            (
                gekoppelde_kostenplaats,
                gekoppelde_kostenplaats
            )
        )

    # =========================
    # FORM DATA
    # =========================
    form.process(
        formdata=request.form if request.method == "POST" else None,
        data={
            **saved_meta,
            "locatie": selected_locatie,
            "kostenplaats": gekoppelde_kostenplaats
        }
    )

    # =========================
    # OPSLAAN
    # =========================
    if request.method == "POST" and "opslaan" in request.form:

        if form.validate_on_submit():

            data["meta"] = {
                "naam_opdracht": form.naam_opdracht.data,
                "locatie": form.locatie.data,
                "kostenplaats": form.kostenplaats.data,
                "wat_opdracht": form.wat_opdracht.data,
                "datum_binnenkomst": form.datum_binnenkomst.data,
                "deadline": form.deadline.data,
                "opdrachtnummer": form.opdrachtnummer.data,
                "telefoonnummer": form.telefoonnummer.data,
                "email": form.email.data,
                "contactpersoon": form.contactpersoon.data,
                "levering": form.levering.data,
                "adres": form.adres.data
            }

            session["data"] = data
            session.modified = True

            flash("Werkbrief opgeslagen", "success")

            return redirect(url_for("producten"))

        flash("Controleer de invoer", "warning")

    return render_template(
        "meta.html",
        form=form,
        budgethouder_locaties=BUDGETHOUDER_LOCATIES,
        locatie_kostenplaats=LOCATIE_KOSTENPLAATS
    )

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
                naam = p.form.naam.data
                bewerking = p.form.bewerking.data
                sub = p.form.subcategorie.data
                if bewerking and not naam:
                    naam = "Bewerking"
                if bewerking == "Inbinden":
                    naam = "Inbinden"
                nieuwe_items.append({
                    "naam": naam,
                    "formaat": p.form.formaat.data,
                    "gram": p.form.gram.data,
                    "zijde": p.form.zijde.data,
                    "aantal": max(1, int(p.form.aantal.data or 1)),
                    "subcategorie": sub,
                    "bewerking": bewerking
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
     with app.app_context():
        db.create_all()
     app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

  
