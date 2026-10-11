"""Small UI smoke test; runs in CI where Streamlit is installed."""
import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit not installed locally')
class StreamlitSmokeTests(unittest.TestCase):
    def test_default_flow_without_api_key(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file('app.py', default_timeout=30).run()
        self.assertFalse(at.exception, 'Default form must render')
        self.assertIn('Angebotsgenerator', at.title[0].value)
        at.button[0].click().run()
        self.assertFalse(at.exception, 'Generating a sample offer must not crash')


if __name__ == '__main__':
    unittest.main()
