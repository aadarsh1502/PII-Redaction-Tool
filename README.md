# PII Redactor

A Python-based tool that detects Personally Identifiable Information (PII) in
Microsoft Word (`.docx`) documents and replaces it with realistic synthetic
values generated using Faker.

## Approach

The tool combines rule-based detection with spaCy NER.

- Regex and validation rules detect structured PII such as emails, phone
  numbers, IP addresses, SSNs, credit cards, dates of birth, and addresses.
- spaCy (`en_core_web_sm`) is used to detect person and company names.
- Faker generates realistic replacement values instead of generic redaction
  labels.
- Repeated occurrences of the same PII value receive the same replacement
  throughout the document.

## Supported PII

Person names, company names, email addresses, phone numbers, physical
addresses, dates of birth, SSNs, credit-card numbers, and IP addresses.

## Tradeoffs and Limitations

Regex-based detection works well for structured PII but may miss unusual
formats. spaCy NER improves name and company detection but can produce false
positives or miss entities, particularly in financial documents and with
unfamiliar names.

Address detection is the most challenging category because addresses can
appear in many different formats. The tool intentionally does not redact
financial reference numbers, order/ticket numbers, or transaction identifiers
unless they match one of the supported PII categories.

Some run-level Word formatting may not be preserved in paragraphs containing
detected PII because redaction is applied at the paragraph-text level.

## Evaluation

The detector was evaluated against a hand-labeled ground-truth dataset using
precision, recall, F1 score, and span-level accuracy.

| Metric | Result |
|---|---:|
| Precision | 96.55% |
| Recall | 93.33% |
| F1 Score | 94.92% |
| Accuracy | 90.32% |

The complete evaluation methodology and results are available in
`evaluation/evaluation_report.md`.

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt

Install the spaCy model:

python -m spacy download en_core_web_sm

Run the redaction script:

python src/scan_document.py

Or launch the Streamlit interface:

python -m streamlit run app.py
Project Structure
PII_Redactor/
├── evaluation/
├── src/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
Live Demo

Streamlit Cloud:
https://pii-redaction-tool-csruphyar5v39qfchsvc4r.streamlit.app/
