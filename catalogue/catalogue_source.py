"""Transcribed from the owner-supplied image-only catalogue, price table page 2.

Prices are INR strings (never floats). Empty/dashed table cells are omitted.
Marketing/medical benefit claims from other pages are intentionally excluded.
The source PDF is local-only and excluded from Docker/Git because it also
contains payment instructions unrelated to the enquiry-only website.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogueItem:
    name: str
    category: str
    prices: tuple[tuple[str, str], ...]
    description: str = ""
    featured: bool = False


ITEMS = (
    CatalogueItem(
        "CP Black Mustard Oil",
        "Cold-Pressed Oils",
        (("500 ml", "250"), ("1 L", "400"), ("5 L", "1750"), ("10 L", "3000")),
        "The catalogue describes oil extracted and packed in airtight bottles after an order is received.",
        True,
    ),
    CatalogueItem(
        "CP Yellow Mustard Oil",
        "Cold-Pressed Oils",
        (("500 ml", "270"), ("1 L", "460"), ("5 L", "2000"), ("10 L", "3500")),
        "The catalogue describes sun-dried, manually cleaned seeds and cold pressing after an order is received. (Catalogue page 8.)",
        True,
    ),
    CatalogueItem(
        "CP Peanut/Groundnut Oil",
        "Cold-Pressed Oils",
        (("500 ml", "360"), ("1 L", "640"), ("5 L", "3000")),
        "The catalogue describes sun-dried peanuts and traditional cold pressing. (Catalogue page 11.)",
        True,
    ),
    CatalogueItem(
        "CP Sunflower Oil",
        "Cold-Pressed Oils",
        (("500 ml", "410"), ("1 L", "730"), ("5 L", "3300")),
    ),
    CatalogueItem(
        "CP Black Sesame (Kala Til) Oil",
        "Cold-Pressed Oils",
        (("100 ml", "250"), ("200 ml", "380"), ("500 ml", "730"), ("1 L", "1300")),
    ),
    CatalogueItem(
        "CP White Sesame (Safed Til) Oil",
        "Cold-Pressed Oils",
        (("100 ml", "130"), ("200 ml", "250"), ("500 ml", "400"), ("1 L", "700")),
        "The catalogue says the oil is extracted after receiving an order. (Catalogue page 13.)",
    ),
    CatalogueItem(
        "CP Flaxseed Oil",
        "Cold-Pressed Oils",
        (("100 ml", "200"), ("200 ml", "280"), ("500 ml", "490"), ("1 L", "900")),
        "The catalogue describes a single-pressed, unrefined oil extracted after an order is received. (Catalogue page 14.)",
    ),
    CatalogueItem(
        "CP Sweet Almond Oil",
        "Cold-Pressed Oils",
        (("100 ml", "710"), ("200 ml", "1250"), ("500 ml", "2950"), ("1 L", "5600")),
        "Listed as cold-pressed sweet almond oil in the catalogue. (Catalogue page 12.)",
    ),
    CatalogueItem(
        "CP Mamra Almond Oil",
        "Cold-Pressed Oils",
        (("100 ml", "1450"), ("200 ml", "2800"), ("500 ml", "6800"), ("1 L", "13000")),
        "Listed as cold-pressed Mamra almond oil in the catalogue. (Catalogue page 12.)",
    ),
    CatalogueItem(
        "CP Black Seed (Kalonji) Oil",
        "Cold-Pressed Oils",
        (("100 ml", "550"), ("200 ml", "900"), ("500 ml", "2150"), ("1 L", "4200")),
    ),
    CatalogueItem(
        "Home Made Desi Ghee - Cow",
        "Ghee & Honey",
        (("500 ml", "760"), ("1 L", "1350"), ("5 L", "6000")),
        "The catalogue describes cow milk cream fermented for 2–3 days, slowly simmered in an iron karahi and packed after an order. (Catalogue page 21.)",
        True,
    ),
    CatalogueItem(
        "Natural Forest Honey",
        "Ghee & Honey",
        (("200 ml", "525"), ("500 ml", "1100"), ("1 L", "1700")),
    ),
    CatalogueItem(
        "Bansi Wheat Flour",
        "Wheat Flours",
        (("5 kg", "1100"), ("10 kg", "1900")),
    ),
    CatalogueItem(
        "Sona Moti Wheat Flour",
        "Wheat Flours",
        (("5 kg", "1600"), ("10 kg", "2800")),
        "The catalogue describes Sona Moti wheat soaked overnight, sun-dried and ground in a low-RPM steel machine. (Catalogue page 15.)",
        True,
    ),
    CatalogueItem(
        "Khapli Wheat Flour",
        "Wheat Flours",
        (("5 kg", "1400"), ("10 kg", "2400")),
        "The catalogue describes naturally grown Khapli wheat ground in a low-RPM steel machine. Minimum order: 5 kg. (Catalogue page 16.)",
    ),
    CatalogueItem(
        "Chana Dal Besan",
        "Pantry Staples",
        (("500 g", "150"), ("1 kg", "260"), ("5 kg", "1500")),
        "The catalogue describes chana dal that is naturally sun-dried and freshly milled. (Catalogue page 19.)",
    ),
    CatalogueItem(
        "Home Grounded Haldi",
        "Pantry Staples",
        (("100 g", "60"), ("250 g", "150"), ("500 g", "300"), ("1 kg", "600")),
        "The catalogue describes turmeric dried in sunlight, hand-pounded and ground in a low-RPM machine. (Catalogue pages 10 and 20.)",
    ),
    CatalogueItem(
        "Desi Arhar (Tur) Dal",
        "Pantry Staples",
        (("500 g", "250"), ("1 kg", "430"), ("5 kg", "2000"), ("10 kg", "3600")),
        "The catalogue describes dry roasting, hand cleaning and stone grinding. (Catalogue page 18.)",
    ),
)

HOME_INTRO = (
    "KT Naturals began with a return to village farming and grew through family and "
    "word of mouth. Explore the catalogue of oils, ghee, honey, flours and pantry staples; "
    "the owner confirms current availability and prices when you enquire."
)
ABOUT = (
    "A journey back to roots\n\n"
    "The KT Naturals catalogue tells how its founder, an Electrical Engineering "
    "graduate of Thapar University, left a seven-year career at Reliance Infrastructure "
    "and returned to his native village. He began growing wheat, mustard and arhar "
    "and sharing the harvest with family across India. Their response inspired KT Naturals.\n\n"
    "The range grew from cold-pressed black mustard oil to other oils, desi ghee, "
    "forest honey, wheat flours, besan, turmeric and arhar dal. The catalogue describes "
    "a small-batch, made-on-order approach. Please ask the owner to confirm current "
    "product details, availability and prices."
)
PHONE = "+91 9329760025"
WHATSAPP_DIGITS = "919329760025"
DELIVERY_AREA = "Pan India delivery (confirm destination and charge with the owner)"
