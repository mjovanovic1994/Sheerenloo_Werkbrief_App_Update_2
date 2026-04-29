from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired
import os
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime
import pdfkit
from flask import make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import logging
import secrets
import gunicorn


app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY is missing")

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
# ---------------- FUNCTIES ----------------

def save_werkbrief_db(data):
    wb = Werkbrief(
        datum=datetime.now().strftime("%Y-%m-%d %H:%M"),
        meta=data.get("meta", {}),
        items=data.get("items", [])
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

def prijs_per_stuk(item):
    key = (
        item.get("naam"),
        item.get("formaat",""),
        item.get("gram",""),
        item.get("zijde","")
    )

    prijs = PRIJZEN.get(key)

    # fallback → subcategorie
    if prijs is None:
        key = (
            item.get("naam"),
            item.get("subcategorie",""),
            "",
            ""
        )
        prijs = PRIJZEN.get(key, 0)

    return prijs

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

# ---------------- FORMS ----------------
class LoginForm(FlaskForm):
    username = StringField("Gebruikersnaam", validators=[DataRequired()])
    password = PasswordField("Wachtwoord", validators=[DataRequired()])
    submit = SubmitField("Inloggen")

class MetaForm(FlaskForm):
    naam_opdracht = StringField("Naam opdracht", validators=[DataRequired()])
    budgethouder = StringField("Budgethouder", validators=[DataRequired()])
    wat_opdracht = TextAreaField("Wat is de opdracht", validators=[DataRequired()])
    datum_binnenkomst = StringField("Datum binnenkomst")
    locatie = StringField("Locatie")
    deadline = StringField("Deadline")
    opdrachtnummer = StringField("Opdrachtnummer")
    kostenplaats = StringField("Kostenplaats")
    telefoonnummer = StringField("Telefoonnummer")
    email = StringField("Email")
    contactpersoon = StringField("Contactpersoon")

    # NIEUW 👇
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

    rendered = render_template(
        "werkbrief.html",
        meta=wb.meta,
        items=wb.items,
        totaal_prijs=0
    )

    try:
        pdf = pdfkit.from_string(rendered, False)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=werkbrief.pdf"
        return response
    except Exception:
        # fallback als wkhtmltopdf niet werkt in productie
        return rendered

@app.route("/werkbrieven")
@login_required
def werkbrieven():
    werkbrieven = Werkbrief.query.order_by(Werkbrief.id.desc()).all()
    return render_template("werkbrieven.html", werkbrieven=werkbrieven)

@app.route("/werkbrief/<int:wb_id>")
@login_required
def werkbrief_detail(wb_id):
    wb = Werkbrief.query.get(wb_id)

    if not wb:
        flash("Werkbrief niet gevonden", "danger")
        return redirect(url_for("werkbrieven"))

    items_met_prijs = []

    for item in wb.items:
        item_copy = item.copy()

        prijs_stuk = prijs_per_stuk(item)
        aantal = max(1, int(item.get("aantal") or 1))

        item_copy["prijs_per_stuk"] = prijs_stuk
        item_copy["prijs"] = prijs_stuk * aantal

        items_met_prijs.append(item_copy)

    totaal = sum(i["prijs"] for i in items_met_prijs)

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

@app.route("/login", methods=["GET","POST"])
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
        else:
            flash("Ongeldige gebruikersnaam of wachtwoord.", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash("Succesvol uitgelogd.", "success")
    return redirect(url_for("login"))

@app.route("/", methods=["GET","POST"])
@login_required
def meta():
    data = get_data()
    form = MetaForm(obj=data.get("meta", {}))
    if form.validate_on_submit():
        data["meta"].update(form.data)
        session.modified = True
        return redirect(url_for("producten"))
    return render_template("meta.html", form=form)

@app.route("/producten", methods=["GET", "POST"])
@login_required
def producten():
    data = get_data()

    # INIT
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

    # ---------------- POST ----------------
    if request.method == "POST":

        # 1 product toevoegen
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

        # verwijderen per card
        elif "remove_product" in request.form:
            idx = int(request.form["remove_product"])
            if 0 <= idx < len(items):
                items.pop(idx)

        # opslaan → DATABASE
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

            wb = Werkbrief(
                datum=datetime.now().strftime("%Y-%m-%d %H:%M"),
                meta=data.get("meta", {}),
                items=nieuwe_items
            )

            db.session.add(wb)
            db.session.commit()

            return redirect(url_for("werkbrieven"))

    # ---------------- GET ----------------
    form = ProductListForm()

    for item in items:
        form.producten.append_entry(item)

    alle_namen = sorted({k[0] for k in PRIJZEN})

    for p in form.producten.entries:
        naam = p.form.naam.data or ""
        formaat = p.form.formaat.data or ""
        gram = p.form.gram.data or ""

        p.form.naam.choices = [("", "-- kies --")] + [(n, n) for n in alle_namen]

        p.form.formaat.choices = [("", "-- kies --")] + [
            (f, f) for f in sorted({k[1] for k in PRIJZEN if not naam or k[0] == naam})
        ]

        p.form.gram.choices = [("", "-- kies --")] + [
            (g, g) for g in sorted({
                k[2] for k in PRIJZEN
                if (not naam or k[0] == naam)
                and (not formaat or k[1] == formaat)
                and k[2]
            })
        ]

        p.form.zijde.choices = [("", "-- kies --")] + [
            (z, z) for z in sorted({
                k[3] for k in PRIJZEN
                if (not naam or k[0] == naam)
                and (not formaat or k[1] == formaat)
                and (not gram or k[2] == gram)
                and k[3]
            })
        ]

    return render_template("producten.html", form=form)

@app.route("/werkbrief")
@login_required
def werkbrief():
    data = get_data()

    items_met_prijs = []

    if "items" not in data:
        data["items"] = []
    
    items_met_prijs = []

    for item in data.get("items", []):
        item_copy = item.copy()

        item_copy["prijs_per_stuk"] = prijs_per_stuk(item)
        item_copy["prijs"] = item_copy["prijs_per_stuk"] * int(item.get("aantal", 1))

        items_met_prijs.append(item_copy)

    totaal = sum(i["prijs"] for i in items_met_prijs)

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
     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

  
