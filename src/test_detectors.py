"""
test_detectors.py
-----------------
Pytest test suite for src/detectors.py.

Run from the project root (PIIenv activated):
    pytest src/test_detectors.py -v

Each PII type has:
  - At least one positive test (should detect the value)
  - At least one negative / false-positive-guard test (should NOT detect)
"""

import sys
import os
import io
import pytest

sys.path.insert(0, os.path.dirname(__file__))

import spacy
from detectors import (
    detect_emails,
    detect_phone_numbers,
    detect_ip_addresses,
    detect_ssns,
    detect_credit_cards,
    detect_dobs,
    detect_addresses,
    detect_ner_entities,
    detect_all_pii,
)


# ---------------------------------------------------------------------------
# Shared spaCy model (loaded once per session for speed)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def nlp():
    return spacy.load(
        "en_core_web_sm",
        exclude=["parser", "tagger", "lemmatizer", "attribute_ruler"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _values(results, pii_type=None):
    """Return set of detected values, optionally filtered by type."""
    if pii_type:
        return {r["value"] for r in results if r["type"] == pii_type}
    return {r["value"] for r in results}


# ===========================================================================
# EMAIL
# ===========================================================================

def test_email_detects_simple():
    text = "Contact us at support@example.com for help."
    results = detect_emails(text)
    assert "support@example.com" in _values(results)


def test_email_detects_subdomain():
    text = "Send reports to user.name@mail.company.org"
    results = detect_emails(text)
    assert "user.name@mail.company.org" in _values(results)


def test_email_does_not_match_plain_url():
    # A bare domain without @ should never be flagged as EMAIL.
    text = "Visit www.example.com for details."
    results = detect_emails(text)
    assert len(results) == 0


# ===========================================================================
# PHONE
# ===========================================================================

def test_phone_detects_indian_landline():
    text = "Telephone: +91 22 4009 4400"
    results = detect_phone_numbers(text)
    assert any("4009 4400" in v for v in _values(results)), _values(results)


def test_phone_detects_international_format():
    text = "Call us at +1-800-555-0199."
    results = detect_phone_numbers(text)
    assert len(results) >= 1


def test_phone_does_not_match_year():
    # A lone 4-digit year should not be flagged as a phone number.
    text = "The company was founded in 1979."
    results = detect_phone_numbers(text)
    assert len(results) == 0


# ===========================================================================
# IP ADDRESS
# ===========================================================================

def test_ip_detects_valid_ipv4():
    text = "Server logs show source IP 192.168.1.100 connecting at midnight."
    results = detect_ip_addresses(text)
    assert "192.168.1.100" in _values(results)


def test_ip_does_not_match_invalid_octet():
    # 999 is not a valid octet - should be rejected.
    text = "Access from 999.0.0.1 was blocked."
    results = detect_ip_addresses(text)
    assert "999.0.0.1" not in _values(results)


# ===========================================================================
# SSN
# ===========================================================================

def test_ssn_detects_standard_format():
    text = "Employee SSN: 523-45-6789 on file."
    results = detect_ssns(text)
    assert "523-45-6789" in _values(results)


def test_ssn_does_not_match_invalid_prefix():
    # SSNs beginning with 000 are invalid and must be rejected.
    text = "Order reference: 000-12-3456 confirmed."
    results = detect_ssns(text)
    assert "000-12-3456" not in _values(results)


def test_ssn_does_not_match_ticket_number():
    # A 7-digit ticket number with dashes in the wrong positions.
    text = "Ticket #: 123-456-7 has been resolved."
    results = detect_ssns(text)
    assert len(results) == 0


# ===========================================================================
# CREDIT CARD
# ===========================================================================

def test_credit_card_detects_spaced_visa():
    text = "Payment made with card 4539 1488 0343 6467."
    results = detect_credit_cards(text)
    assert "4539 1488 0343 6467" in _values(results)


def test_credit_card_detects_unspaced_visa():
    text = "Refund issued to Visa card number 4111111111111111."
    results = detect_credit_cards(text)
    assert "4111111111111111" in _values(results)


def test_credit_card_does_not_match_luhn_fail():
    # 1234567890123456 fails Luhn checksum - must not be flagged.
    text = "Transaction volume: 1234567890123456 units processed."
    results = detect_credit_cards(text)
    assert "1234567890123456" not in _values(results)


def test_credit_card_does_not_match_share_quantity():
    # Large financial quantities should not be flagged as credit cards.
    text = "The company issued 5000000000000000 shares in the IPO."
    results = detect_credit_cards(text)
    assert len(results) == 0


# ===========================================================================
# DATE OF BIRTH
# ===========================================================================

def test_dob_detects_born_keyword():
    text = "born on 15 March 1970"
    results = detect_dobs(text)
    assert any("1970" in v for v in _values(results)), _values(results)


def test_dob_detects_date_of_birth_label():
    text = "Date of Birth: 12/05/1968"
    results = detect_dobs(text)
    assert any("1968" in v for v in _values(results)), _values(results)


def test_dob_does_not_match_unlabeled_date():
    # A date with no DOB context keyword should not be flagged.
    text = "The AGM was held on 10 December 2025."
    results = detect_dobs(text)
    assert len(results) == 0


# ===========================================================================
# ADDRESS
# ===========================================================================

def test_address_detects_flat_prefix():
    text = "Flat No. 102, Sai Complex Shaniwar Peth, Pune - 411 030 Maharashtra, India"
    results = detect_addresses(text)
    expected = "Flat No. 102, Sai Complex Shaniwar Peth, Pune - 411 030 Maharashtra, India"
    assert expected in _values(results), _values(results)


def test_address_detects_multiword_road_prefix():
    # "Senapati Bapat Road" - two words before "Road" must all be captured.
    text = "Senapati Bapat Road, behind Sahara Hotel, Shivajinagar, Model Colony, Pune - 411 016, Maharashtra, India"
    results = detect_addresses(text)
    assert any("Senapati Bapat Road" in v for v in _values(results)), _values(results)


def test_address_captures_full_trailing_locality():
    # "Deccan Gymkhana" is a two-word locality that must appear in the span.
    text = "Flat - 1, S. no. 245/ 104, Prabhat Road Lane no. 3, Shivaji Nagar, Deccan Gymkhana, Pune - 411 004, Maharashtra, India"
    results = detect_addresses(text)
    assert any("Deccan Gymkhana" in v for v in _values(results)), _values(results)


def test_address_does_not_match_building_process():
    text = "The building process was completed ahead of schedule."
    results = detect_addresses(text)
    assert len(results) == 0


def test_address_does_not_match_roadshow():
    text = "We will conduct a road show across five cities next quarter."
    results = detect_addresses(text)
    assert len(results) == 0


def test_address_does_not_overshoot_newline():
    # The match must stop at the newline; "E-mail" on the next line must NOT
    # be included in the address value.
    text = (
        "Flat No. 102, Sai Complex Shaniwar Peth, Pune - 411 030 Maharashtra, India\n"
        "E-mail: hingnetare@gmail.com"
    )
    results = detect_addresses(text)
    assert all("E-mail" not in v for v in _values(results)), _values(results)


# ===========================================================================
# PERSON (NER)
# ===========================================================================

def test_person_detects_full_name(nlp):
    text = "Sarthak Malvadkar is the Company Secretary."
    results = detect_ner_entities(text, nlp)
    assert any(
        r["type"] == "PERSON" and "Malvadkar" in r["value"]
        for r in results
    ), results


def test_person_detects_multiple_names(nlp):
    text = (
        "Kushal Subbayya Hegde, Rajesh Kushal Hegde, Rohit Kushal Hegde "
        "and Rakhi Girija Shetty are Executive Directors."
    )
    results = detect_ner_entities(text, nlp)
    person_values = {r["value"] for r in results if r["type"] == "PERSON"}
    assert "Kushal Subbayya Hegde" in person_values, person_values


def test_person_does_not_match_offer_price_phrase(nlp):
    # "Offer Price" is a financial term and must NOT be flagged as a person.
    text = "The Offer Price was determined by the book-building process."
    results = detect_ner_entities(text, nlp)
    person_values = {r["value"].lower() for r in results if r["type"] == "PERSON"}
    assert "offer price" not in person_values, person_values


def test_person_does_not_match_single_word_all_caps(nlp):
    # All-caps single tokens like "CEO" must not be flagged as a person.
    text = "The CEO announced the results."
    results = detect_ner_entities(text, nlp)
    person_values = {r["value"].lower() for r in results if r["type"] == "PERSON"}
    assert "ceo" not in person_values, person_values


# ===========================================================================
# COMPANY (NER)
# ===========================================================================

def test_company_detects_named_entity(nlp):
    text = "Nuvama Wealth Management Limited is the lead manager."
    results = detect_ner_entities(text, nlp)
    assert any(
        r["type"] == "COMPANY" and "Nuvama" in r["value"]
        for r in results
    ), results


def test_company_does_not_match_regulatory_term(nlp):
    # "SEBI" in a regulatory sentence should not be a standalone COMPANY hit.
    text = "As per SEBI guidelines, the offer must comply with all regulations."
    results = detect_ner_entities(text, nlp)
    company_values = {r["value"].lower() for r in results if r["type"] == "COMPANY"}
    assert "sebi" not in company_values, company_values


# ===========================================================================
# INTEGRATION - detect_all_pii
# ===========================================================================

def test_detect_all_pii_contact_line(nlp):
    """Full pipeline: a single contact-info line should yield PERSON, PHONE."""
    text = (
        "Contact Person: Sarthak Malvadkar, Company Secretary; "
        "Telephone: + 91 20 4505 3237"
    )
    results = detect_all_pii(text, nlp)
    types_found = {r["type"] for r in results}
    assert "PERSON" in types_found, results
    assert "PHONE" in types_found, results


def test_detect_all_pii_email_and_phone(nlp):
    """Email and phone detected together without interference."""
    text = "Email: ksh.ipo@nuvama.com\nTelephone: +91 22 4009 4400"
    results = detect_all_pii(text, nlp)
    values = _values(results)
    assert "ksh.ipo@nuvama.com" in values, values
    assert any("4009 4400" in v for v in values), values


def test_detect_all_pii_no_duplicate_spans(nlp):
    """
    No two detections may overlap in position (span-level deduplication).
    The same email at two different positions is legitimately detected twice —
    the invariant is no duplicate spans, not no duplicate values.
    """
    text = "E-mail: test@example.com and again test@example.com here."
    results = detect_all_pii(text, nlp)
    # Every result must occupy a unique (start, end) span.
    spans = [(r["start"], r["end"]) for r in results]
    assert len(spans) == len(set(spans)), f"Duplicate spans found: {spans}"
    # Both occurrences of the email should be detected (at different offsets).
    email_values = [r["value"] for r in results if r["type"] == "EMAIL"]
    assert len(email_values) == 2, (
        f"Expected 2 email detections (one per occurrence), got: {email_values}"
    )


# ===========================================================================
# ORIGINAL NER PRINT-DEMO (preserved as a test)
# ===========================================================================

def test_ner_demo_rashi_patil_rohan_dey(nlp):
    """
    The original print-demo scenario from the old test_detectors.py.
    Validates that known persons and companies in that snippet are detected
    and that financial boilerplate is filtered.
    """
    text = """
Rashi Patil works at KSH International Limited.

Rohan Dey contacted ICICI Securities Limited.

John Smith works for Microsoft Corporation.

Offer Price was announced by the company.

The Net Proceeds will be used for the Offer.

Kirtane & Pandit LLP is the auditor.
"""

    results = detect_ner_entities(text, nlp)

    # Print the results the same way the old script did, for visibility.
    out = io.StringIO()
    out.write("FILTERED NER DETECTIONS\n")
    out.write("=" * 50 + "\n")
    for r in results:
        out.write(str(r) + "\n")
    out.write("=" * 50 + "\n")
    out.write(f"Total detections: {len(results)}\n")
    print(out.getvalue())  # visible with pytest -s

    # Assertions: at least some persons/companies were found.
    types_found = {r["type"] for r in results}
    assert "PERSON" in types_found or "COMPANY" in types_found, (
        "Expected at least one PERSON or COMPANY in the NER demo text"
    )

    # "Offer Price" must NOT appear as a detected person.
    person_values = {r["value"].lower() for r in results if r["type"] == "PERSON"}
    assert "offer price" not in person_values, (
        f"Offer Price was incorrectly flagged as PERSON: {person_values}"
    )
