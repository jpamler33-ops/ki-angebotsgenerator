# Angebotsgenerator für Handwerker — Pilot-MVP

Ein kostenlos lokal startbarer, deutschsprachiger Angebotsgenerator mit exakter Positionsrechnung, PDF-Angebot, kopierbarer Kunden-E-Mail und Nachfass-Nachricht. **Die Grundfunktionen erfordern keinen API-Key.** Optional kann OpenAI eine E-Mail sprachlich verbessern; Preise und PDF werden niemals von KI berechnet.

## Starten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Optional: `.env.example` als `.env` kopieren und einen eigenen `OPENAI_API_KEY` setzen. Niemals Schlüssel einchecken oder veröffentlichen.

Für Windows PowerShell statt der Zeile \`source ...\` verwenden:

~~~powershell
.\\.venv\\Scripts\\Activate.ps1
~~~

## Agent-Skills

- Das mitgelieferte \`AGENTS.md\` legt projektweite Coding-Regeln fest.
- Der eigene Skill \`.agents/skills/offer-quality-gate/SKILL.md\` definiert die Tests für Angebote.
- **Optional, separat installieren:** Superpowers (Grok Build CLI: \`grok plugin install superpowers@xai-official --trust\`; Claude Code: \`/plugin install superpowers@claude-plugins-official\`).
- UI/UX Pro Max nur bei Designarbeiten ergänzen (\`npx ui-ux-pro-max-cli init --ai universal\`).
- Externe Skills sind **nicht** durch diese Dateien automatisch installiert. Nur aus vertrauenswürdigen Quellen und nach Prüfung der Berechtigungen installieren.

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