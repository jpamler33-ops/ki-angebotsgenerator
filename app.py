import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

st.set_page_config(
    page_title="KI-Angebotsgenerator für Handwerker",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ KI-Angebotsgenerator für Handwerker")
st.write("Erstelle in wenigen Minuten ein professionelles Angebot plus Kunden-E-Mail.")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Bitte setze deinen OPENAI_API_KEY in einer .env Datei.")
    st.code("OPENAI_API_KEY=dein_api_key_hier", language="bash")
    st.stop()

client = OpenAI(api_key=api_key)

model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_offer_text(data: dict) -> str:
    prompt = f"""
Du bist ein professioneller Büroassistent für deutsche Handwerksbetriebe.

Erstelle ein seriöses, klares und verkaufsstarkes Angebot auf Deutsch.

Wichtig:
- Nicht übertreiben.
- Professionell, aber verständlich schreiben.
- Keine erfundenen Rabatte.
- Keine rechtlich riskanten Aussagen.
- Preise exakt aus den übergebenen Daten übernehmen.
- Der Text soll für kleine Handwerksbetriebe geeignet sein.

Daten:

Firma:
{data["company_name"]}
{data["company_address"]}
Ansprechpartner: {data["contact_person"]}
Telefon/E-Mail: {data["company_contact"]}

Kunde:
{data["customer_name"]}
{data["customer_address"]}

Projekt:
{data["project_title"]}

Beschreibung:
{data["project_description"]}

Positionen:
{data["items_text"]}

Zwischensumme netto: {data["net_total"]}
MwSt: {data["vat_amount"]}
Gesamtsumme brutto: {data["gross_total"]}

Ausführungszeitraum:
{data["timeline"]}

Angebot gültig bis:
{data["valid_until"]}

Bitte erstelle:

1. ANGEBOTSTEXT
Mit Begrüßung, Projektbeschreibung, Leistungsübersicht, Preisübersicht und freundlichem Abschluss.

2. E-MAIL AN DEN KUNDEN
Kurz, freundlich und professionell.

3. FOLLOW-UP NACHRICHT
Für den Fall, dass der Kunde nach 5 Tagen noch nicht geantwortet hat.
"""

    response = client.responses.create(
        model=model,
        input=prompt
    )

    return response.output_text


with st.sidebar:
    st.header("Firmendaten")
    company_name = st.text_input("Firmenname", "Müller Haustechnik GmbH")
    company_address = st.text_area("Firmenadresse", "Musterstraße 12\n10115 Berlin")
    contact_person = st.text_input("Ansprechpartner", "Max Müller")
    company_contact = st.text_input("Telefon/E-Mail", "030 12345678 | info@mueller-haustechnik.de")

st.subheader("1. Kundendaten")

col1, col2 = st.columns(2)

with col1:
    customer_name = st.text_input("Kundenname", "Thomas Schneider")
    customer_address = st.text_area("Kundenadresse", "Beispielweg 8\n10117 Berlin")

with col2:
    project_title = st.text_input("Projektname", "Badsanierung")
    timeline = st.text_input("Ausführungszeitraum", "voraussichtlich innerhalb von 2–3 Wochen nach Auftragserteilung")
    valid_until = st.date_input("Angebot gültig bis", date.today() + timedelta(days=14))

st.subheader("2. Projektbeschreibung")

project_description = st.text_area(
    "Was soll gemacht werden?",
    "Komplette Modernisierung eines Badezimmers inklusive Demontage alter Sanitärobjekte, Vorbereitung der Anschlüsse und Montage neuer Elemente.",
    height=120
)

st.subheader("3. Positionen")

default_items = [
    {"Position": "Demontage alter Sanitärobjekte", "Menge": 1.0, "Einheit": "Pauschal", "Einzelpreis netto": 450.00},
    {"Position": "Montage Waschbecken", "Menge": 1.0, "Einheit": "Stk.", "Einzelpreis netto": 280.00},
    {"Position": "Montage WC", "Menge": 1.0, "Einheit": "Stk.", "Einzelpreis netto": 320.00},
    {"Position": "Material und Kleinteile", "Menge": 1.0, "Einheit": "Pauschal", "Einzelpreis netto": 390.00},
]

items = st.data_editor(
    default_items,
    num_rows="dynamic",
    use_container_width=True
)

vat_rate = st.number_input("MwSt. in %", min_value=0.0, max_value=30.0, value=19.0, step=1.0)

net_total = 0.0
items_text_lines = []

for item in items:
    try:
        position = item["Position"]
        menge = float(item["Menge"])
        einheit = item["Einheit"]
        einzelpreis = float(item["Einzelpreis netto"])
        total = menge * einzelpreis
        net_total += total

        items_text_lines.append(
            f"- {position}: {menge} {einheit} x {euro(einzelpreis)} = {euro(total)} netto"
        )
    except Exception:
        continue

vat_amount = net_total * (vat_rate / 100)
gross_total = net_total + vat_amount

st.subheader("4. Kalkulation")

c1, c2, c3 = st.columns(3)

c1.metric("Netto", euro(net_total))
c2.metric("MwSt.", euro(vat_amount))
c3.metric("Brutto", euro(gross_total))

if st.button("🚀 Angebot generieren"):
    if not customer_name or not project_title or net_total <= 0:
        st.error("Bitte Kundennamen, Projektnamen und mindestens eine gültige Position eintragen.")
    else:
        with st.spinner("Angebot wird erstellt..."):
            data = {
                "company_name": company_name,
                "company_address": company_address,
                "contact_person": contact_person,
                "company_contact": company_contact,
                "customer_name": customer_name,
                "customer_address": customer_address,
                "project_title": project_title,
                "project_description": project_description,
                "items_text": "\n".join(items_text_lines),
                "net_total": euro(net_total),
                "vat_amount": euro(vat_amount),
                "gross_total": euro(gross_total),
                "timeline": timeline,
                "valid_until": valid_until.strftime("%d.%m.%Y"),
            }

            result = generate_offer_text(data)

        st.success("Fertig!")
        st.subheader("Generiertes Angebot")
        st.text_area("Ergebnis", result, height=700)

        st.download_button(
            label="📄 Als TXT herunterladen",
            data=result,
            file_name=f"angebot_{customer_name.replace(' ', '_').lower()}.txt",
            mime="text/plain"
        )
