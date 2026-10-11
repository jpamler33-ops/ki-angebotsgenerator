import unittest
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from offer_engine import (OfferValidationError, calculate_quote, build_offer_text,
                          generate_offer_pdf, euro)


def data():
    return dict(company_name='Änderung & Söhne GmbH', company_address='Straße 1\n92224 Amberg',
                company_contact='kontakt@example.de', customer_name='Kunde GmbH',
                customer_address='Allee 2', project_title='Treppe erneuern',
                project_description='Holztreppe reparieren und Ölen',
                timeline='nach Vereinbarung', valid_until=date.today()+timedelta(days=14),
                created_on=date.today(), contact_person='Ansprechpartner')


def rows():
    return [{'Position':'Leistung','Menge':'2','Einheit':'Stk.','Einzelpreis netto':'10,05'}]


class QuoteTests(unittest.TestCase):
    def test_happy_path(self):
        quote = calculate_quote(rows(), 19)
        self.assertEqual((quote.net, quote.vat, quote.gross),
                         (Decimal('20.10'), Decimal('3.82'), Decimal('23.92')))

    def test_half_up_currency_rounding(self):
        quote = calculate_quote([{'Position':'Test','Menge':'0,5','Einheit':'h',
                                  'Einzelpreis netto':'0,01'}], '0')
        self.assertEqual(quote.net, Decimal('0.01'))

    def test_german_thousands(self):
        quote = calculate_quote([{'Position':'Test','Menge':'1','Einheit':'Stk.',
                                  'Einzelpreis netto':'1.234,56'}], 0)
        self.assertEqual(quote.net, Decimal('1234.56'))
        self.assertEqual(euro(quote.net), '1.234,56 €')

    def test_zero_quantity_rejected(self):
        bad=rows(); bad[0]['Menge']='0'
        with self.assertRaises(OfferValidationError): calculate_quote(bad, 19)

    def test_invalid_row_must_not_be_skipped(self):
        bad=rows()+[{'Position':'', 'Menge':'1', 'Einheit':'h', 'Einzelpreis netto':'5'}]
        with self.assertRaises(OfferValidationError): calculate_quote(bad, 19)

    def test_nan_infinite_negative_and_precision_rejected(self):
        for value in ['NaN','Infinity','-1','1.001','abc']:
            with self.subTest(value=value):
                bad=rows(); bad[0]['Einzelpreis netto']=value
                with self.assertRaises(OfferValidationError): calculate_quote(bad, 19)

    def test_vat_range(self):
        with self.assertRaises(OfferValidationError): calculate_quote(rows(), 31)

    def test_text_contains_identical_totals(self):
        q=calculate_quote(rows(), 19)
        txt=build_offer_text(data(), q)
        for amount in ('20,10 €','3,82 €','23,92 €'):
            self.assertIn(amount, txt)

    def test_pdf_generated_and_text_extractable(self):
        from pypdf import PdfReader
        q=calculate_quote(rows(), 19)
        binary=generate_offer_pdf(data(), q)
        self.assertTrue(binary.startswith(b'%PDF-'))
        doc=PdfReader(BytesIO(binary))
        content='\n'.join(p.extract_text() for p in doc.pages)
        self.assertIn('23,92', content)
        self.assertIn('Kunde GmbH', content)

    def test_long_description_wraps(self):
        q=calculate_quote([{'Position':'Schrauben und Montage ' * 18,'Menge':1,
                            'Einheit':'Pauschal','Einzelpreis netto':'45'}]*15, 19)
        pdf=generate_offer_pdf(data(), q)
        self.assertTrue(pdf.startswith(b'%PDF-'))


if __name__ == '__main__':
    unittest.main()
