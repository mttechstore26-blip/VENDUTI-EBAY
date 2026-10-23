"""Offline regression tests for eBay tablet/eReader classification; zero API credits."""
import unittest

from tablet_taxonomy import classify_tablet


class TabletTaxonomyTests(unittest.TestCase):
    def check(self, title, brand, model, state=None):
        actual = classify_tablet(title)
        self.assertEqual(actual[0], brand, title)
        self.assertIn(model, actual[2], title)
        if state:
            self.assertIn(state, actual[3], title)

    def test_ipad_generation_and_configuration(self):
        self.check("Apple iPad 10a generazione 64GB WiFi", "Apple", "iPad 10ª gen.")
        self.check("iPad 10 256GB Cellular", "Apple", "iPad 10ª gen.")
        self.check("Apple iPad A2696 WiFi 64GB", "Apple", "iPad 10ª gen.")
        self.check("iPad mini 6 64GB", "Apple", "iPad mini 6ª gen.")
        self.check("iPad Air A2588 256GB", "Apple", "iPad Air 5ª gen.")
        self.assertIn("128 GB", classify_tablet("Samsung Galaxy Tab S9 FE 128GB")[2])
        self.assertNotEqual(classify_tablet("iPad 10 64GB")[2], classify_tablet("iPad 10 256GB")[2])

    def test_kindle_generations(self):
        self.check("Kindle Paperwhite 12th 16GB", "Amazon", "12ª gen.")
        self.check("Kindle Paperwhite Signature Edition 2024", "Amazon", "Signature Edition 12ª gen.")
        self.check("Kindle Paperwhite 11th 8GB", "Amazon", "11ª gen.")
        self.check("Kindle Scribe 2022", "Amazon", "Scribe (2022)")
        self.check("Kindle Colorsoft", "Amazon", "Colorsoft")

    def test_kobo_from_official_model_numbers(self):
        self.check("Kobo Clara BW N365", "Kobo", "Clara BW")
        self.check("Kobo Clara Colour N367", "Kobo", "Clara Colour")
        self.check("Kobo Libra Colour N428", "Kobo", "Libra Colour")
        self.check("Kobo Elipsa 2E", "Kobo", "Elipsa 2E")
        self.check("Kobo Libra 2", "Kobo", "Libra 2")

    def test_other_readers(self):
        self.check("PocketBook InkPad Color 3 PB743K3", "PocketBook", "InkPad Color 3")
        self.check("PocketBook Era Color", "PocketBook", "Era Color")
        self.check("Onyx BOOX Note Air 3 C", "BOOX", "Note Air 3 C")
        self.check("reMarkable 2", "reMarkable", "reMarkable 2")

    def test_tablets(self):
        self.check("Samsung Galaxy Tab S9 FE+ 128GB", "Samsung", "S9 FE+")
        self.check("Samsung Galaxy Tab S9 FE 128GB", "Samsung", "S9 FE")
        self.check("Lenovo Tab P11 Pro Gen 2", "Lenovo", "P11 Pro Gen 2")
        self.check("Microsoft Surface Go 3 128GB", "Microsoft", "Surface Go 3")
        self.check("Xiaomi Redmi Pad SE", "Xiaomi", "Redmi Pad SE")

    def test_flags_and_safe_unknowns(self):
        self.check("Kobo Clara BW Custodia", "Kobo", "Clara BW", "Accessorio")
        self.check("iPad 10 64GB MDM bloccato", "Apple", "iPad 10ª gen.", "bloccato")
        self.check("Lotto 3 Kindle Paperwhite", "Amazon", "Paperwhite", "Lotto")
        self.check("iPad Air senza indicazione generazione", "Apple", "da verificare")
        self.check("Tablet android 10 pollici", "Non identificato", "Modello da identificare")


if __name__ == "__main__":
    unittest.main()
