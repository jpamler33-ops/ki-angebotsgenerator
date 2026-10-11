# Angebotsgenerator für Handwerker — Pilot-MVP

Ein kostenlos lokal startbarer, deutschsprachiger Angebotsgenerator mit exakter Positionsrechnung, PDF-Angebot, kopierbarer Kunden-E-Mail und Nachfass-Nachricht. **Die Grundfunktionen erfordern keinen API-Key.** Optional kann OpenAI eine E-Mail sprachlich verbessern; Preise und PDF werden niemals von KI berechnet.

## Starten

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Optional: `.env.example` als `.env` kopieren und einen eigenen `OPENAI_API_KEY` setzen. Niemals Schlüssel einchecken oder veröffentlichen.

## Testen

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py offer_engine.py
```

## Pilot mit 10 Handwerksbetrieben

1. Produkt mit ausschließlich fiktiven Daten demonstrieren; niemandem unaufgefordert Kundendaten abfordern.
2. Zehn Betriebe fragen, wie lange sie aktuell für ein Angebot benötigen, was sie nutzen und wie oft Fehler entstehen.
3. Drei Betriebe eine Demo machen lassen; protokollieren, ob sie ein echtes, korrigiertes PDF erstellen können.
4. Erst danach nach Zahlungsbereitschaft fragen. **Kein Umsatz oder Kundennachweis vorhanden.**

## Risiken / Grenzen

- Die App ist ein Prototyp, kein geprüftes Buchhaltungs-/Rechtstool. Steuersatz, Leistungsbeschreibung, Angebotsfristen und rechtliche Pflichtangaben müssen Nutzer selbst verifizieren.
- Die Demo enthält absichtlich Muster-Personen und Beispielpreise. Vor dem Versand austauschen.
- Keine Nutzerverwaltung, Mandantentrennung, automatische Zustellung oder dauerhafte Speicherung; daher **nicht** als öffentlich erreichbaren Multi-Tenant-Service mit echten Kundendaten betreiben.
- PDF wird serverseitig erzeugt und direkt heruntergeladen. KI-Option übermittelt den E-Mail-Entwurf an den eingestellten Anbieter.