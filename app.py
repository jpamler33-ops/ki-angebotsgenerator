"""Handwerker-Angebote: numerically safe, usable without a paid AI API."""
import os
import hashlib
import json
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from offer_engine import (OfferValidationError, build_email, build_followup,
                          build_offer_text, calculate_quote, euro, generate_offer_pdf)

load_dotenv()
st.set_page_config(page_title='Angebotsgenerator für Handwerker', page_icon='📄', layout='wide')
st.title('Angebotsgenerator für Handwerker')
st.caption('Kostenlose Angebotskalkulation und PDF-Erstellung. KI optional – kein API-Key nötig.')

with st.sidebar:
    st.header('Firmendaten')
    company_name = st.text_input('Firmenname', 'Müller Haustechnik GmbH')
    company_address = st.text_area('Firmenadresse', 'Musterstraße 12\n10115 Berlin')
    contact_person = st.text_input('Ansprechpartner', 'Max Müller')
    company_contact = st.text_input('Telefon/E-Mail', '030 12345678 | info@mueller-haustechnik.de')

st.subheader('1. Kunde und Auftrag')
col1, col2 = st.columns(2)
with col1:
    customer_name = st.text_input('Kundenname', 'Thomas Schneider')
    customer_address = st.text_area('Kundenadresse', 'Beispielweg 8\n10117 Berlin')
with col2:
    project_title = st.text_input('Projektname', 'Badsanierung')
    timeline = st.text_input('Ausführungszeitraum', 'nach Vereinbarung')
    valid_until = st.date_input('Angebot gültig bis', date.today() + timedelta(days=14), min_value=date.today())

st.subheader('2. Leistungsbeschreibung')
project_description = st.text_area('Beschreibung',
    'Modernisierung eines Badezimmers inklusive Demontage und Montage der genannten Sanitärobjekte.',
    height=100)
st.subheader('3. Angebotspositionen')
items = st.data_editor([
    {'Position':'Demontage alter Sanitärobjekte','Menge':1.0,'Einheit':'Pauschal','Einzelpreis netto':450.00},
    {'Position':'Montage Waschbecken','Menge':1.0,'Einheit':'Stk.','Einzelpreis netto':280.00},
    {'Position':'Montage WC','Menge':1.0,'Einheit':'Stk.','Einzelpreis netto':320.00},
    {'Position':'Material und Kleinteile','Menge':1.0,'Einheit':'Pauschal','Einzelpreis netto':390.00},
], num_rows='dynamic', use_container_width=True)
vat_rate = st.number_input('MwSt. in % (bitte korrekten Steuersatz selbst prüfen)',
                           min_value=0.0, max_value=30.0, value=19.0, step=1.0)

try:
    quote = calculate_quote(items, vat_rate)
    valid = True
except OfferValidationError as exc:
    st.error(str(exc))
    valid = False

if valid:
    st.subheader('4. Kalkulation')
    c1,c2,c3 = st.columns(3)
    c1.metric('Netto', euro(quote.net))
    c2.metric('MwSt.', euro(quote.vat))
    c3.metric('Brutto', euro(quote.gross))

# Prevent silently downloading an older PDF after the user edits the form.
input_signature = hashlib.sha256(json.dumps({
    'company_name': company_name, 'company_address': company_address,
    'contact_person': contact_person, 'company_contact': company_contact,
    'customer_name': customer_name, 'customer_address': customer_address,
    'project_title': project_title, 'timeline': timeline,
    'valid_until': valid_until.isoformat(), 'project_description': project_description,
    'items': items, 'vat_rate': vat_rate,
}, sort_keys=True, default=str).encode('utf-8')).hexdigest()

st.info('Demo mit Beispieldaten: Vor dem Versand alle Namen, Preise, Steuersätze, Leistungen und Fristen überprüfen. Keine Rechts- oder Steuerprüfung.')

if st.button('Angebot erstellen', type='primary', disabled=not valid):
    data = dict(company_name=company_name, company_address=company_address,
        contact_person=contact_person, company_contact=company_contact,
        customer_name=customer_name, customer_address=customer_address,
        project_title=project_title, timeline=timeline,
        valid_until=valid_until, created_on=date.today(),
        project_description=project_description)
    try:
        if valid_until < date.today():
            raise OfferValidationError('Das Gültigkeitsdatum liegt in der Vergangenheit.')
        text = build_offer_text(data, quote)
        pdf = generate_offer_pdf(data, quote)
    except (OfferValidationError, ValueError) as exc:
        st.error(str(exc))
    else:
        st.session_state['result'] = dict(signature=input_signature, data=data, text=text, pdf=pdf,
                                          email=build_email(data), followup=build_followup(data))

result = st.session_state.get('result')
if result and result.get('signature') != input_signature:
    result = None
    st.warning('Eingaben geändert: Bitte das Angebot neu erstellen, damit die Downloads aktuell sind.')
if result:
    st.success('Angebot erstellt. Bitte vor dem Versenden prüfen.')
    st.download_button('PDF herunterladen', result['pdf'], file_name='angebot.pdf', mime='application/pdf')
    st.download_button('TXT herunterladen', result['text'], file_name='angebot.txt', mime='text/plain')
    st.text_area('Angebotstext', result['text'], height=310)
    st.text_area('E-Mail-Vorlage', result['email'], height=190)
    st.text_area('Nachfass-Nachricht', result['followup'], height=190)

    if os.getenv('OPENAI_API_KEY'):
        if st.button('Optional: Kunden-E-Mail sprachlich verbessern (KI)'):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
                response = client.responses.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
                    instructions=('Verbessere ausschließlich Sprache und Höflichkeit der folgenden deutschen '
                                  'Kunden-E-Mail. Erfinde keine Fakten, Konditionen, Rabatte oder Preise. '
                                  'Antworte nur mit der E-Mail.'),
                    input=result['email'],
                )
                st.text_area('KI-Formulierung (manuell prüfen)', response.output_text, height=210)
            except Exception:
                st.error('KI-Dienst gerade nicht verfügbar. Die berechneten Angebotsdaten bleiben unverändert.')
