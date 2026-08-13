import re
import ipaddress
from dateparser import parse


# ============================================================
# EMAIL
# ============================================================

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


def detect_emails(text):
    results = []

    for match in EMAIL_PATTERN.finditer(text):
        results.append({
            "type": "EMAIL",
            "value": match.group(),
            "start": match.start(),
            "end": match.end(),
        })

    return results


# ============================================================
# PHONE
# ============================================================

PHONE_PATTERN = re.compile(
    r"""
    (?<!\d)
    (?:
        \+?\d{1,3}[\s.-]?
    )?
    (?:
        \d{2,5}[\s.-]?
    )?
    \d{3,4}[\s.-]?
    \d{3,4}
    (?!\d)
    """,
    re.VERBOSE,
)


def detect_phone_numbers(text):
    results = []

    for match in PHONE_PATTERN.finditer(text):
        value = match.group().strip()
        digits = re.sub(r"\D", "", value)

        if value.count(".") == 3:
            continue

        if len(digits) < 10 or len(digits) > 15:
            continue

        results.append({
            "type": "PHONE",
            "value": value,
            "start": match.start(),
            "end": match.end(),
        })

    return results


# ============================================================
# IP ADDRESS
# ============================================================

IP_PATTERN = re.compile(
    r"(?<![\d.])"
    r"(?:\d{1,3}\.){3}\d{1,3}"
    r"(?![\d.])"
)


def detect_ip_addresses(text):
    results = []

    for match in IP_PATTERN.finditer(text):
        value = match.group()

        try:
            ipaddress.ip_address(value)
        except ValueError:
            continue

        results.append({
            "type": "IP_ADDRESS",
            "value": value,
            "start": match.start(),
            "end": match.end(),
        })

    return results


# ============================================================
# SSN
# ============================================================

SSN_PATTERN = re.compile(
    r"(?<![\d-])"
    r"(?!000|666|9\d{2})"
    r"\d{3}-"
    r"(?!00)"
    r"\d{2}-"
    r"(?!0000)"
    r"\d{4}"
    r"(?![\d-])"
)


def detect_ssns(text):
    results = []

    for match in SSN_PATTERN.finditer(text):
        results.append({
            "type": "SSN",
            "value": match.group(),
            "start": match.start(),
            "end": match.end(),
        })

    return results


# ============================================================
# CREDIT CARD
# ============================================================

CREDIT_CARD_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\d[ -]?){13,19}"
    r"(?!\d)"
)


def luhn_check(number):
    digits = [int(d) for d in number]

    checksum = 0
    parity = len(digits) % 2

    for i, digit in enumerate(digits):

        if i % 2 == parity:
            digit *= 2

            if digit > 9:
                digit -= 9

        checksum += digit

    return checksum % 10 == 0


def detect_credit_cards(text):
    results = []

    for match in CREDIT_CARD_PATTERN.finditer(text):

        value = match.group()

        digits = re.sub(r"[ -]", "", value)

        if not 13 <= len(digits) <= 19:
            continue

        if not luhn_check(digits):
            continue

        results.append({
            "type": "CREDIT_CARD",
            "value": value,
            "start": match.start(),
            "end": match.end(),
        })

    return results


# ============================================================
# DATE OF BIRTH
# ============================================================

DOB_CONTEXT_PATTERN = re.compile(
    r"""
    (?:
        date\s+of\s+birth
        |
        d\.?\s*o\.?\s*b\.?
        |
        born(?:\s+on)?
    )
    \s*(?::|-)?\s*
    (
        \d{1,2}[/-]\d{1,2}[/-]\d{4}
        |
        \d{1,2}\s+
        (?:January|February|March|April|May|June|
        July|August|September|October|November|December)
        \s+\d{4}
        |
        (?:January|February|March|April|May|June|
        July|August|September|October|November|December)
        \s+\d{1,2},?\s+\d{4}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def detect_dobs(text):
    results = []

    for match in DOB_CONTEXT_PATTERN.finditer(text):

        date_value = match.group(1)

        parsed_date = parse(
            date_value,
            settings={
                "STRICT_PARSING": True
            }
        )

        if parsed_date is None:
            continue

        results.append({
            "type": "DOB",
            "value": date_value,
            "start": match.start(1),
            "end": match.end(1),
        })

    return results


# ============================================================
# ADDRESS DETECTOR
# ============================================================

def detect_addresses(text):

    results = []

    # Trailing segment pattern: `[^\n,]{1,60}` matches an entire comma-
    # delimited token including spaces (e.g. "Deccan Gymkhana", "Madhya Pradesh").
    # Newline containment is handled by iterating over text.splitlines() below.
    _SEG = r"[^\n,]{1,60}"   # one comma-delimited address segment

    address_pattern = re.compile(
        rf"""
        (?P<full_match>
            # ── Flat / Office / Unit / Plot / House / Building ──────────────
            (?:
                (?:Flat|Office|Unit|Plot|House|Building)\s+(?:No\.?\s*)?
                [A-Za-z0-9./ -]{{1,20}}      # unit designator e.g. "102" or "- 1"
                (?:\s*,\s*{_SEG}){{0,14}}    # trailing city/state segments
            )
            |
            # ── Road / Street / Lane / Marg / Nagar / Colony ────────────────
            # Allow up to 3 space-joined tokens BEFORE the keyword so
            # "Senapati Bapat Road" is matched in full (not just "Bapat Road").
            (?:
                [A-Za-z0-9./&'()-]+
                (?:\s+[A-Za-z0-9./&'()-]+){{0,2}}
                \s+
                (?:Road|Rd\.?|Street|St\.?|Lane|Ln\.?|Marg|Nagar|Colony)
                (?:\s*,\s*{_SEG}){{0,14}}
            )
            |
            # ── Complex / Chambers / Bhavan / Park ──────────────────────────
            (?:
                [A-Za-z0-9./&'()-]+
                (?:\s+[A-Za-z0-9./&'()-]+){{0,2}}
                \s+
                (?:Chambers|Complex|Bhavan|Park)
                (?:\s*,\s*{_SEG}){{0,14}}
            )
        )
        """,
        re.IGNORECASE | re.VERBOSE
    )

    invalid_context = {
        "road show",
        "road shows",
        "roadshow",
        "roadshows",
        "frequently asked questions",
        "investor meeting",
        "meeting schedules",
        "marketing",
        "relations strategy",
        "book building",
        "bidding terminals",
        "mock trading",
        "anchor coordination",
        "statutory auditors",
        "building process",
    }

    for line in text.splitlines():
        for match in address_pattern.finditer(line):
            value = match.group("full_match").strip().rstrip(".,;:")

            if len(value) < 12:
                continue

            normalized = re.sub(r"\s+", " ", value.lower())

            if any(phrase in normalized for phrase in invalid_context):
                continue

            has_address_indicator = bool(re.search(
                r"\b(road|rd|street|st|lane|ln|marg|nagar|colony|flat|office|unit|plot|house|building|chambers|complex|bhavan|park)\b",
                normalized, re.IGNORECASE
            ))

            if not has_address_indicator:
                continue

            has_number = bool(re.search(r"\b\d+[A-Za-z]?(?:-\d+)?\b", normalized))

            location_words = {"pune", "mumbai", "bhopal", "maharashtra", "india", "shivaji", "nagar", "erandawane", "deccan", "gymkhana", "taloja", "chakan", "khed", "panvel", "raigad", "peth", "residency"}
            has_location = any(word in normalized.split() for word in location_words)

            if not has_number and not has_location:
                continue

            start_index = text.find(value, match.start())
            results.append({
                "type": "ADDRESS",
                "value": value,
                "start": start_index,
                "end": start_index + len(value),
            })

    return results


# ============================================================
# NER FILTERING
# ============================================================

PERSON_EXCLUSIONS = {
    "offer",
    "prospectus",
    "particulars",
    "date",
    "company",
    "bankers",
    "registrar",
    "monitoring agency",
    "sponsor banker",
    "key managerial",
    "key managerial personnel",
    "cap price",
    "floor price",
    "bid amount",
    "share transfer agents",
    "registered broker",
    "stockbrokers",
    "mutual funds",
    "secondary transfer",
    "acknowledgement slip",
    "schedule xiii",
    "corrigenda thereto",
    "independent director",
    "independent director(s",
    "wilful defaulter",
    "bill",
    "air conditioning",
    "mega volt-amperes",
    "photo voltaic",
    "non-gaap measures",
    "operational",
    "gopal bo",
    "reference rate",
    "selling shareholder",
    "upi bidders",
    "upi circulars",
    "individual bidders",
    "qib bidders",
    "registered brokers",
    "stock exchanges",
    "collectively",
    "telephone",
    "website",
    "circulars",
    "high voltage direct",
    "gram jyoti",
    "kisan urja suraksha",
    "waterloo industrial",
    "waterloo motors",
    "our company",
    "buena monte",
    "pushpakamal apartment",
}


LOCATION_WORDS = {
    "road",
    "street",
    "lane",
    "nagar",
    "colony",
    "complex",
    "bhavan",
    "marg",
    "taluka",
    "district",
    "village",
    "town",
    "city",
    "showroom",
    "hospital",
    "facility",
    "park",
    "branch",
    "office",
    "east",
    "west",
    "north",
    "south",
    "opposite",
    "opp",
    "house",
    "chambers",
    "flat",
    "ground",
    "floor",
    "pune",
    "mumbai",
    "website",
}


DOCUMENT_WORDS = {
    "offer",
    "price",
    "bid",
    "share",
    "shares",
    "transfer",
    "account",
    "amount",
    "bankers",
    "banker",
    "registrar",
    "particulars",
    "schedule",
    "regulation",
    "regulations",
    "circular",
    "circulars",
    "committee",
    "director",
    "directors",
    "personnel",
    "company",
    "prospectus",
    "measure",
    "measures",
    "bidders",
    "bidder",
    "stock",
    "exchanges",
    "collectively",
    "operational",
    "telephone",
    "website",
}


# ============================================================
# PERSON VALIDATION
# ============================================================

def is_valid_person(entity_text):

    text = entity_text.strip()

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower()
    )

    if not text:
        return False

    # --------------------------------------------------------
    # Exact false positives
    # --------------------------------------------------------

    if normalized in PERSON_EXCLUSIONS:
        return False

    # --------------------------------------------------------
    # Reject common NER garbage containing these phrases
    # --------------------------------------------------------

    invalid_phrases = {
        "registered broker",
        "selling shareholder",
        "reference rate",
        "waterloo industrial",
        "upi bidders",
        "individual bidders",
        "qib bidders",
        "stock exchanges",
        "air conditioning",
        "high voltage direct",
        "kisan urja suraksha",
        "gram jyoti",
        "c operational",
    }

    if any(
        phrase in normalized
        for phrase in invalid_phrases
    ):
        return False

    words = text.split()

    # --------------------------------------------------------
    # A normal person name should have at least two words
    # --------------------------------------------------------

    if len(words) < 2:
        return False

    # --------------------------------------------------------
    # Names should not contain digits
    # --------------------------------------------------------

    if any(char.isdigit() for char in text):
        return False

    # --------------------------------------------------------
    # Reject location/document terminology
    # --------------------------------------------------------

    clean_words = [
        re.sub(r"[^\w]", "", word).lower()
        for word in words
    ]

    if any(
        word in LOCATION_WORDS
        for word in clean_words
    ):
        return False

    if any(
        word in DOCUMENT_WORDS
        for word in clean_words
    ):
        return False

    # --------------------------------------------------------
    # Reject company/legal terminology
    # --------------------------------------------------------

    company_terms = {
        "llp",
        "limited",
        "ltd",
        "private",
        "corporation",
        "inc",
        "incorporated",
        "company",
        "huf",
        "associates",
    }

    if any(
        word in company_terms
        for word in clean_words
    ):
        return False

    # --------------------------------------------------------
    # Reject words that are strongly associated with
    # addresses, documents, or roles
    # --------------------------------------------------------

    bad_person_words = {
        "rate",
        "shareholder",
        "shareholders",
        "bidder",
        "bidders",
        "broker",
        "brokers",
        "website",
        "telephone",
        "circular",
        "circulars",
        "industrial",
        "operational",
        "conditioning",
        "voltage",
        "direct",
        "bill",
        "bank",
        "banker",
        "stock",
        "exchange",
        "account",
        "capital",
        "market",
        "division",
        "registered",
        "committee",
        "director",
        "directors",

        # NEW: common NER false positives in financial documents
        "circuit",
        "kilometers",
        "kilometres",
        "cagr",
        "margin",
        "promoter",
        "promoters",
        "trust",
        "trusts",
        "electricals",
        "process",
        "building",
        "floor",
        "unit",
    }

    if any(
        word in bad_person_words
        for word in clean_words
    ):
        return False

    # --------------------------------------------------------
    # Reject strings ending in "Website"
    # --------------------------------------------------------

    if normalized.endswith(" website"):
        return False

    # --------------------------------------------------------
    # Reject long all-uppercase phrases.
    #
    # Keep legitimate uppercase names such as:
    # KUSHAL SUBBAYYA HEGDE
    #
    # but reject long document fragments.
    # --------------------------------------------------------

    letters_only = re.sub(
        r"[^A-Za-z]",
        "",
        text
    )

    if (
        letters_only
        and letters_only.isupper()
        and len(words) >= 5
    ):
        return False

    # --------------------------------------------------------
    # Candidate should consist primarily of alphabetic words.
    #
    # Allow initials such as:
    # K.
    # N.
    # R.
    # --------------------------------------------------------

    for word in words:

        cleaned = word.strip(".,'-")

        if not cleaned:
            continue

        # Initial such as K. / N.
        if re.fullmatch(
            r"[A-Za-z]\.",
            cleaned
        ):
            continue

        # Normal alphabetic name
        if not re.fullmatch(
            r"[A-Za-z]+\.?",
            cleaned
        ):
            return False

    return True


# ============================================================
# PERSON SPAN RECOVERY  (BUG FIX)
# ------------------------------------------------------------
# spaCy's NER sometimes greedily extends a PERSON span to include a
# trailing role/title word when there's no comma separating the name
# from the title (e.g. table cells like "Sarthak Malvadkar Company
# Secretary and Compliance Officer"). When that happens, the extra
# word (e.g. "Company") trips is_valid_person's DOCUMENT_WORDS /
# company_terms filters and the ENTIRE entity — including the real
# name — gets thrown away.
#
# Fix: if the full entity fails validation, try trimming up to 2
# trailing words and re-validate the shorter candidate. If a trimmed
# version passes, use it (with correctly adjusted character offsets)
# instead of discarding the entity outright.
# ============================================================

def _try_trim_person(entity_text, start_char, max_trim=2):
    """
    Attempt to recover a valid person name by trimming trailing words
    from an over-greedy NER span. Returns (value, start, end) if a
    trimmed candidate validates, else None.
    """
    words = entity_text.split()

    for trim in range(1, max_trim + 1):
        remaining = len(words) - trim

        if remaining < 2:
            break

        candidate = " ".join(words[:remaining])

        if is_valid_person(candidate):
            end_char = start_char + len(candidate)
            return candidate, start_char, end_char

    return None


# ============================================================
# TRAILING JUNK CHARACTER RECOVERY  (BUG FIX)
# ------------------------------------------------------------
# Names followed directly by footnote/decoration characters with no
# space (e.g. "Kushal Subbayya Hegde*^&", common in table footnote
# markers) sometimes get mislabeled ORG instead of PERSON by spaCy's
# small model. Since is_valid_company() then correctly rejects them
# (no legal-suffix keyword), the name is dropped entirely.
#
# Fix: for ORG entities that fail is_valid_company, strip trailing
# non-alphanumeric junk and see if what's left looks like a valid
# person name. If so, reclassify it as PERSON.
# ============================================================

_TRAILING_JUNK_PATTERN = re.compile(r"[\*\^&#@~`|\\/+=<>\[\]{}!]+$")


def _strip_trailing_junk(text):
    return _TRAILING_JUNK_PATTERN.sub("", text).strip()


# ============================================================
# COMPANY VALIDATION
# ============================================================

COMPANY_EXCLUSIONS = {
    "llp",
    "limited",
    "ltd",
    "private",
    "corporation",
    "inc",
    "inc.",
    "pvt",
    "pvt ltd",
    "bank limited",
    "advisory private limited",
    "corporate office",
    "our company",
    "registered brokers",
    "stockbrokers",
    "stock exchanges",
    "collectively",
    "public offer account",
    "independent director",
    "independent director(s",
    "capital market division",
    "bank",
    "bank limited",
}


COMPANY_KEYWORDS = {
    "limited",
    "ltd",
    "private limited",
    "pvt ltd",
    "llp",
    "corporation",
    "corp",
    "inc.",
    "inc",
    "associates",
}


# ------------------------------------------------------------
# Obvious non-company phrases
# ------------------------------------------------------------

COMPANY_INVALID_PHRASES = {
    "our company",
    "corporate office",
    "registered brokers",
    "stockbrokers",
    "stock exchanges",
    "public offer account",
    "capital market division",
    "independent director",
    "independent director(s",
    "bank limited",
    "advisory private limited",
    "gross national disposable income",
}


def is_valid_company(entity_text):

    text = entity_text.strip()

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower()
    )

    if not text:
        return False

    # --------------------------------------------------------
    # Exact exclusions
    # --------------------------------------------------------

    if normalized in COMPANY_EXCLUSIONS:
        return False

    # --------------------------------------------------------
    # Obvious false-positive phrases
    # --------------------------------------------------------

    if any(
        phrase in normalized
        for phrase in COMPANY_INVALID_PHRASES
    ):
        return False

    if len(text) < 4:
        return False

    # --------------------------------------------------------
    # Reject address fragments
    # --------------------------------------------------------

    address_words = {
        "ground floor",
        "flat no",
        "flat number",
        "opposite",
        "opp",
        "road",
        "street",
        "lane",
        "chambers",
        "house",
        "branch",
        "office",
    }

    if any(
        phrase in normalized
        for phrase in address_words
    ):
        return False

    words = normalized.split()

    # --------------------------------------------------------
    # Remove legal suffixes when checking whether the
    # company contains meaningful words.
    # --------------------------------------------------------

    legal_words = {
        "limited",
        "ltd",
        "private",
        "pvt",
        "llp",
        "corporation",
        "corp",
        "inc",
        "inc.",
    }

    meaningful_words = [
        word
        for word in words
        if word.strip(".,()") not in legal_words
    ]

    if not meaningful_words:
        return False

    # --------------------------------------------------------
    # A company should have a recognizable corporate keyword
    # --------------------------------------------------------

    has_company_keyword = any(
        keyword in normalized
        for keyword in COMPANY_KEYWORDS
    )

    if not has_company_keyword:
        return False

    # --------------------------------------------------------
    # Reject obvious document/address terminology
    # --------------------------------------------------------

    invalid_company_words = {
        "office",
        "account",
        "bank",
        "bankers",
        "broker",
        "brokers",
        "stock",
        "exchange",
        "exchanges",
        "committee",
        "director",
        "directors",
        "collectively",
        "website",
        "telephone",
        "ground",
        "floor",
    }

    # Only reject if these appear as standalone words.
    #
    # Example:
    # "HDFC Bank Limited" should NOT be rejected just because
    # it contains "Bank", because it is a legitimate company.
    #
    # Therefore only apply this to obviously malformed entities.
    if normalized in {
        "bank limited",
        "advisory private limited",
        "corporate office",
    }:
        return False

    # --------------------------------------------------------
    # Basic character validation
    # --------------------------------------------------------

    if not re.search(r"[A-Za-z]", text):
        return False

    return True


# ============================================================
# COMPANY NAME REGISTRY  (BUG FIX — company-consistency pass)
# ------------------------------------------------------------
# is_valid_company() intentionally requires a legal-suffix keyword
# (Limited, Ltd, LLP, ...) before accepting a company name — this
# keeps precision high and avoids false positives on generic terms
# like "the Company" or "Registered Office".
#
# But real documents always shorten a company's name after its first
# full mention ("ICICI Securities Limited" -> later just "ICICI
# Securities"), and those shortened repeat mentions have no suffix
# to validate against, so they were being silently dropped.
#
# CompanyNameRegistry fixes this WITHOUT loosening is_valid_company's
# core rule: it remembers every company name that DID validate with
# its full legal suffix, derives the shortened form, and then looks
# for that exact shortened form elsewhere in the document. Only
# names already confirmed once (in their full, suffixed form) get
# this treatment — brand-new/unconfirmed short phrases are still
# never accepted, so precision is preserved.
# ============================================================

_LEGAL_SUFFIX_TRIM_PATTERN = re.compile(
    r"\s+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|"
    r"Corporation|Corp\.?|Inc\.?|Associates)\s*$",
    re.IGNORECASE,
)


class CompanyNameRegistry:
    """
    Tracks canonical (full, legal-suffix-validated) company names seen
    across a document, and finds later/earlier informal repeat mentions
    of those same names so they can be redacted consistently.

    Usage pattern (see integration note at bottom of file):
        registry = CompanyNameRegistry()

        # Pass 1 — warm up the registry using the FULL document text,
        # so shortened mentions that appear BEFORE their full-suffix
        # counterpart are still caught.
        registry.warm_up(full_document_text, nlp)

        # Pass 2 — normal per-paragraph redaction loop, passing the
        # warmed registry into detect_all_pii each time.
        for paragraph_text in paragraphs:
            results = detect_all_pii(paragraph_text, nlp, company_registry=registry)
    """

    def __init__(self):
        # short_form (lowercase) -> canonical full name (as first seen)
        self._canonical = {}

    def register(self, full_company_name):
        """Record a validated full-suffix company name."""
        short = _LEGAL_SUFFIX_TRIM_PATTERN.sub("", full_company_name).strip()

        if not short or short.lower() == full_company_name.strip().lower():
            return

        key = short.lower()

        if key not in self._canonical:
            self._canonical[key] = full_company_name.strip()

    def warm_up(self, full_text, nlp):
        """
        Run NER once over the ENTIRE document text purely to populate
        the registry with every full-suffix company name, regardless
        of where in the document it first appears. This guarantees
        shortened mentions are caught even if they occur earlier in
        the document than their full-suffix counterpart.
        """
        doc = nlp(full_text)

        for entity in doc.ents:
            if entity.label_ != "ORG":
                continue

            entity_text = entity.text.strip()

            if is_valid_company(entity_text):
                self.register(entity_text)

    def find_shortened_mentions(self, text):
        """
        Scan `text` for standalone occurrences of any registered
        shortened company name and return them as COMPANY detections.
        Each result carries a `canonical` field so the caller's fake-
        value mapper can map both the full and short form to the SAME
        fake company name.
        """
        results = []

        for short_lower, canonical in self._canonical.items():
            pattern = re.compile(
                r"\b" + re.escape(short_lower) + r"\b",
                re.IGNORECASE,
            )

            for match in pattern.finditer(text):
                results.append({
                    "type": "COMPANY",
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "canonical": canonical,
                })

        return results


# ============================================================
# NER DETECTOR
# ============================================================

def detect_ner_entities(text, nlp, company_registry=None):

    doc = nlp(text)

    results = []

    for entity in doc.ents:

        entity_text = entity.text.strip()

        # ----------------------------------------------------
        # PERSON
        # ----------------------------------------------------

        if entity.label_ == "PERSON":

            if is_valid_person(entity_text):

                results.append({
                    "type": "PERSON",
                    "value": entity_text,
                    "start": entity.start_char,
                    "end": entity.end_char,
                })

            else:
                # BUG FIX: try recovering a valid name by trimming a
                # greedily-attached trailing title/role word.
                trimmed = _try_trim_person(
                    entity_text,
                    entity.start_char,
                )

                if trimmed:
                    value, start, end = trimmed
                    results.append({
                        "type": "PERSON",
                        "value": value,
                        "start": start,
                        "end": end,
                    })

        # ----------------------------------------------------
        # ORGANIZATION -> COMPANY
        # ----------------------------------------------------

        elif entity.label_ == "ORG":

            if is_valid_company(entity_text):

                results.append({
                    "type": "COMPANY",
                    "value": entity_text,
                    "start": entity.start_char,
                    "end": entity.end_char,
                })

                if company_registry is not None:
                    company_registry.register(entity_text)

            else:
                # BUG FIX: names followed by trailing footnote/junk
                # characters (e.g. "Kushal Subbayya Hegde*^&") are
                # sometimes mislabeled ORG instead of PERSON. Strip
                # the junk and see if what's left is a valid name.
                stripped = _strip_trailing_junk(entity_text)

                if stripped != entity_text and is_valid_person(stripped):
                    end_char = entity.start_char + len(stripped)
                    results.append({
                        "type": "PERSON",
                        "value": stripped,
                        "start": entity.start_char,
                        "end": end_char,
                    })

    # --------------------------------------------------------
    # BUG FIX: company-consistency pass — catch shortened repeat
    # mentions of companies already confirmed elsewhere via their
    # full, legal-suffix name (requires a warmed-up registry).
    # --------------------------------------------------------

    if company_registry is not None:
        shortened_hits = company_registry.find_shortened_mentions(text)

        for hit in shortened_hits:
            if not _overlaps(hit, results):
                results.append(hit)

    # --------------------------------------------------------
    # Keep document order
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item["start"]
    )

    return results


# ============================================================
# OVERLAP
# ============================================================

def _overlaps(result, existing_results):

    for existing in existing_results:

        if (
            result["start"] < existing["end"]
            and result["end"] > existing["start"]
        ):
            return True

    return False


# ============================================================
# MASTER DETECTOR
# ============================================================

def detect_all_pii(text, nlp=None, company_registry=None):
    """
    company_registry is OPTIONAL and fully backward compatible:
    existing calls like detect_all_pii(text, nlp) behave exactly as
    before. Pass a warmed-up CompanyNameRegistry to additionally catch
    shortened/informal repeat mentions of companies already confirmed
    elsewhere in the document (see CompanyNameRegistry docstring).
    """

    results = []

    # --------------------------------------------------------
    # Specific / regex-based detectors
    # --------------------------------------------------------
    detectors = [
        detect_addresses,
        detect_ip_addresses,
        detect_credit_cards,
        detect_ssns,
        detect_dobs,
        detect_emails,
        detect_phone_numbers,
    ]

    for detector in detectors:

        detections = detector(text)

        for detection in detections:

            if not _overlaps(
                detection,
                results
            ):
                results.append(detection)

    # --------------------------------------------------------
    # NER-based detectors
    # PERSON + COMPANY
    # --------------------------------------------------------
    if nlp is not None:

        ner_results = detect_ner_entities(
            text,
            nlp,
            company_registry=company_registry,
        )

        for detection in ner_results:

            if not _overlaps(
                detection,
                results
            ):
                results.append(detection)

    # --------------------------------------------------------
    # Document order
    # --------------------------------------------------------
    results.sort(
        key=lambda item: item["start"]
    )

    return results
