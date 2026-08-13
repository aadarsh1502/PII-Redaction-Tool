# PII-Redaction-Tool

PII Redactor

A Python-based tool that detects Personally Identifiable Information (PII) in Microsoft Word (.docx) documents and replaces detected values with realistic synthetic alternatives generated using Faker.

Approach

The detector uses a combination of rule-based regex detection and spaCy NER:

Regex/rule-based detection is used for structured PII such as emails, phone numbers, IP addresses, SSNs, credit-card numbers, dates of birth, and physical addresses.
spaCy NER (en_core_web_sm) is used to detect person names and company/organization names.
Faker generates realistic replacement values instead of generic [REDACTED] placeholders.
Repeated occurrences of the same PII value are replaced with the same generated value throughout the document to maintain consistency.
Tradeoffs and Limitations

Regex-based detection provides good precision for structured PII but can miss unusual formats. spaCy NER improves detection of names and companies but can produce false positives or miss entities, especially in financial documents and unfamiliar Indian names.

Address detection is the most challenging category because addresses can have many different formats. The tool intentionally does not redact financial reference numbers, order/ticket numbers, or transaction identifiers unless they represent one of the supported PII categories.

When PII is detected inside a paragraph, the paragraph text is replaced with the anonymized text, so some run-level Word formatting such as bold, italics, or hyperlinks may not be preserved for that paragraph.

Supported PII Types
Person names
Company names
Email addresses
Phone numbers
Physical addresses
Dates of birth
Social Security Numbers (SSNs)
Credit-card numbers
IP addresses
Running the Tool

Install the dependencies:

pip install -r requirements.txt

Install the spaCy model:

python -m spacy download en_core_web_sm

Run the redaction script:

python src/scan_document.py

The project also includes a Streamlit interface for uploading a .docx file, detecting PII, anonymizing it, and downloading the processed document.

Evaluation

The detector was evaluated against a hand-labeled ground-truth dataset using precision, recall, F1 score, and span-level accuracy. The complete evaluation methodology, results, error analysis, and per-record breakdown are available in:

evaluation/evaluation_report.md
