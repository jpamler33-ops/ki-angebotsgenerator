"""Deterministic quotation calculations and PDF export. No AI may alter prices."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from xml.sax.saxutils import escape

CENT = Decimal('0.01')


class OfferValidationError(ValueError):
    """The quotation contains invalid or incomplete input."""


def decimal_value(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise OfferValidationError(f'{field}: bitte eine gültige Zahl eingeben.')
    s = str(value).strip().replace('\u00a0', '').replace(' ', '')
    # Common German input '1.234,56'; plain decimal '1234.56' remains valid.
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        result = Decimal(s)
    except (InvalidOperation, ValueError):
        raise OfferValidationError(f'{field}: bitte eine gültige Zahl eingeben.') from None
    if not result.is_finite():
        raise OfferValidationError(f'{field}: bitte eine endliche Zahl eingeben.')
    return result


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def euro(value: Decimal) -> str:
    v = money(value)
    return f'{v:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.') + ' €'


@dataclass(frozen=True)
class OfferItem:
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return money(self.quantity * self.unit_price)


@dataclass(frozen=True)
class Quote:
    items: tuple[OfferItem, ...]
    vat_rate: Decimal
    net: Decimal
    vat: Decimal
    gross: Decimal


def calculate_quote(rows: list[dict], vat_rate: object) -> Quote:
    rate = decimal_value(vat_rate, field='MwSt.')
    if not Decimal('0') <= rate <= Decimal('30'):
        raise OfferValidationError('MwSt.: Wert muss zwischen 0 und 30 % liegen.')
    if not rows:
        raise OfferValidationError('Mindestens eine Angebotsposition ist erforderlich.')

    items = []
    for i, row in enumerate(rows, start=1):
        prefix = f'Position {i}'
        description = str(row.get('Position') or '').strip()
        unit = str(row.get('Einheit') or '').strip()
        if not description or not unit:
            raise OfferValidationError(f'{prefix}: Bezeichnung und Einheit sind erforderlich.')
        qty = decimal_value(row.get('Menge'), field=f'{prefix} Menge')
        price = decimal_value(row.get('Einzelpreis netto'), field=f'{prefix} Preis')
        if qty <= 0 or price < 0:
            raise OfferValidationError(f'{prefix}: Menge muss > 0 und Preis >= 0 sein.')
        if price.as_tuple().exponent < -2:
            raise OfferValidationError(f'{prefix}: Einzelpreis darf höchstens zwei Nachkommastellen haben.')
        items.append(OfferItem(description, qty, unit, price))

    net = sum((i.line_total for i in items), Decimal('0.00'))
    vat = money(net * rate / Decimal('100'))
    return Quote(tuple(items), rate, net, vat, net + vat)


def required_text(value: str, field: str) -> str:
    v = value.strip()
    if not v:
        raise OfferValidationError(f'{field} ist erforderlich.')
    return v


def build_offer_text(data: dict, quote: Quote) -> str:
    company = required_text(data['company_name'], 'Firmenname')
    customer = required_text(data['customer_name'], 'Kundenname')
    title = required_text(data['project_title'], 'Projektname')
    lines = [
        company, data['company_address'].strip(), data['company_contact'].strip(), '',
        f'An: {customer}', data['customer_address'].strip(), '',
        f'ANGEBOT – {title}', f'Erstellt am: {data["created_on"].strftime("%d.%m.%Y")}',
        f'Gültig bis: {data["valid_until"].strftime("%d.%m.%Y")}', '',
        'Sehr geehrte Damen und Herren,',
        'vielen Dank für Ihre Anfrage. Gerne bieten wir folgende Leistungen an:', '',
        data['project_description'].strip(), '',
        'LEISTUNGSÜBERSICHT',
    ]
    for index, item in enumerate(quote.items, start=1):
        lines.append(f'{index}. {item.description} – {item.quantity} {item.unit} × {euro(item.unit_price)} = {euro(item.line_total)} netto')
    lines += [
        '', f'Nettosumme: {euro(quote.net)}',
        f'MwSt. ({quote.vat_rate.normalize()} %): {euro(quote.vat)}',
        f'Gesamtsumme: {euro(quote.gross)}', '',
        f'Geplanter Ausführungszeitraum: {data["timeline"].strip() or "nach Vereinbarung"}', '',
        'Bei Fragen zum Angebot stehen wir gerne zur Verfügung.',
        'Mit freundlichen Grüßen', data['contact_person'].strip() or company,
    ]
    return '\n'.join(lines)


def build_email(data: dict) -> str:
    return (f'Betreff: Ihr Angebot – {data["project_title"].strip()}\n\n'
            f'Guten Tag {data["customer_name"].strip()},\n\n'
            'anbei erhalten Sie unser Angebot zu Ihrem Projekt. '
            'Bei Rückfragen oder Anpassungswünschen melden Sie sich gerne.\n\n'
            f'Mit freundlichen Grüßen\n{data["contact_person"].strip() or data["company_name"].strip()}')


def build_followup(data: dict) -> str:
    return (f'Betreff: Rückfrage zu unserem Angebot – {data["project_title"].strip()}\n\n'
            f'Guten Tag {data["customer_name"].strip()},\n\n'
            'ich wollte kurz nachfragen, ob Sie unser Angebot erhalten haben '
            'und ob noch Fragen offen sind. Wir freuen uns auf Ihre Rückmeldung.\n\n'
            f'Mit freundlichen Grüßen\n{data["contact_person"].strip() or data["company_name"].strip()}')


def generate_offer_pdf(data: dict, quote: Quote) -> bytes:
    """Produces an A4 PDF entirely from verified user inputs and Decimal totals."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

    def p(value: object, style):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), style)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=19*mm, bottomMargin=18*mm, title='Angebot')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyDE', parent=styles['Normal'], leading=15, spaceAfter=6))
    styles.add(ParagraphStyle(name='TitleDE', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=13))
    styles.add(ParagraphStyle(name='SmallDE', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#475569')))
    styles.add(ParagraphStyle(name='RightDE', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=10))
    normal, small, title, right = [styles[k] for k in ['BodyDE', 'SmallDE', 'TitleDE', 'RightDE']]

    flow = [p(required_text(data['company_name'], 'Firmenname'), title),
            p(data['company_address'].strip() + '\n' + data['company_contact'].strip(), small), Spacer(1, 10*mm),
            p(required_text(data['customer_name'], 'Kundenname'), normal),
            p(data['customer_address'].strip(), normal), Spacer(1, 6*mm),
            p('ANGEBOT – ' + required_text(data['project_title'], 'Projektname'), title),
            p('Erstellt am: ' + data['created_on'].strftime('%d.%m.%Y') +
              '     |     Gültig bis: ' + data['valid_until'].strftime('%d.%m.%Y'), small),
            Spacer(1, 5*mm),
            p('Vielen Dank für Ihre Anfrage. Wir bieten Ihnen folgende Leistungen an:', normal),
            p(data['project_description'].strip(), normal), Spacer(1, 5*mm)]

    available = A4[0] - 36*mm
    table_rows = [[p(x, small) for x in ['Pos.', 'Leistung', 'Menge', 'Einzel netto', 'Summe netto']]]
    for i, item in enumerate(quote.items, start=1):
        table_rows.append([p(i, normal), p(item.description, normal),
                           p(f'{item.quantity} {item.unit}', normal),
                           p(euro(item.unit_price), normal), p(euro(item.line_total), normal)])
    table = Table(table_rows, colWidths=[available*.07, available*.38, available*.18,
                                         available*.18, available*.19], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#edf2f7')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#b8c4d1')),
        ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#e2e8f0')),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    flow += [table, Spacer(1, 6*mm)]
    flow.append(KeepTogether([
        p('Nettosumme: ' + euro(quote.net), right),
        p(f'MwSt. ({quote.vat_rate.normalize()} %): ' + euro(quote.vat), right),
        p('GESAMTSUMME: ' + euro(quote.gross), right),
        Spacer(1, 5*mm),
        p('Ausführungszeitraum: ' + (data['timeline'].strip() or 'nach Vereinbarung'), normal),
        Spacer(1, 5*mm),
        p('Bei Rückfragen stehen wir Ihnen gerne zur Verfügung.', normal),
        p('Mit freundlichen Grüßen', normal),
        p(data['contact_person'].strip() or data['company_name'].strip(), normal),
    ]))

    def page_number(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawRightString(A4[0]-18*mm, 10*mm, f'Seite {document.page}')

    doc.build(flow, onFirstPage=page_number, onLaterPages=page_number)
    return buffer.getvalue()
