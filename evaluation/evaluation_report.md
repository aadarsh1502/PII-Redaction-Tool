# PII Detection Evaluation Report

> **Accuracy definition**: `TP / (TP + FP + FN)` — the Jaccard/IoU metric for span detection. Standard accuracy (with true negatives) does not apply here because the universe of non-PII text is effectively unbounded and there is no fixed set of negative examples.

---

## Per-Type Metrics

| PII Type       | TP | FP | FN | Precision | Recall |   F1   | Accuracy |
|----------------|----|----|----|-----------|--------|--------|----------|
| ADDRESS        |  4 |  1 |  1 |    80.00% | 80.00% | 80.00% |   66.67% |
| COMPANY        |  1 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| CREDIT_CARD    |  2 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| DOB            |  2 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| EMAIL          |  6 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| IP_ADDRESS     |  1 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| PERSON         |  7 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |
| PHONE          |  4 |  0 |  1 |   100.00% | 80.00% | 88.89% |   80.00% |
| SSN            |  1 |  0 |  0 |   100.00% | 100.00% | 100.00% |  100.00% |

## Overall Metrics

| Metric    | Value    |
|-----------|----------|
| TP        |       28 |
| FP        |        1 |
| FN        |        2 |
| Precision |   96.55% |
| Recall    |   93.33% |
| F1        |   94.92% |
| Accuracy  |   90.32% |

---

## Per-Record Breakdown

### P1
**Correctly detected (TP):**
- `[PERSON]` `Sarthak Malvadkar`
- `[PHONE]` `91 20 4505 3237`

### P2
**Correctly detected (TP):**
- `[EMAIL]` `cs.connect@kshinternational.com`

### P3
**Correctly detected (TP):**
- `[PERSON]` `Kushal Subbayya Hegde`
- `[PERSON]` `Rajesh Kushal Hegde`
- `[PERSON]` `Rohit Kushal Hegde`

### P4
**Correctly detected (TP):**
- `[PERSON]` `Amod Joshi`
- `[PERSON]` `Sandesh Bhagwat`
- `[PERSON]` `Sarthak Malvadkar`

### T1
**Correctly detected (TP):**
- `[EMAIL]` `ksh.ipo@nuvama.com`
- `[PHONE]` `+91 22 4009 4400`

### T2
**Correctly detected (TP):**
- `[EMAIL]` `ksh@icicisecurities.com`
- `[PHONE]` `+91 22 6807 7100`

### T3
**Correctly detected (TP):**
- `[EMAIL]` `kshinternational.ipo@in.mpms.mufg.com`

**Missed (FN):**
- `[PHONE]` `+91 81081 14949`

### T4
**Correctly detected (TP):**
- `[COMPANY]` `Nuvama Wealth Management Limited`
- `[EMAIL]` `ksh.ipo@nuvama.com`
- `[PHONE]` `+91 22 40094400`

**False positives (FP):**
- `[ADDRESS]` `Building No 3, Inspire BKC, G Block, Bandra Kurla Complex, Bandra East, Mumbai 400051, Maharashtra, India`

**Missed (FN):**
- `[ADDRESS]` `Building No 3, Inspire BKC, G Block, Bandra Kurla Complex, Bandra East, Mumbai 400051, Maharashtra`

### T5
**Correctly detected (TP):**
- `[ADDRESS]` `Flat - 1, S. no. 245/ 104, Prabhat Road Lane no. 3, Shivaji Nagar, Deccan Gymkhana, Pune - 411 004, Maharashtra, India`

### T6
**Correctly detected (TP):**
- `[ADDRESS]` `Senapati Bapat Road, behind Sahara Hotel, Shivajinagar, Model Colony, Pune - 411 016, Maharashtra, India`

### T7
**Correctly detected (TP):**
- `[ADDRESS]` `JK Road, Minal Residency, Huzur, Govindpura, Bhopal - 462 023, Madhya Pradesh, India`

### T8
**Correctly detected (TP):**
- `[ADDRESS]` `Flat No. 102, Sai Complex Shaniwar Peth, Pune - 411 030 Maharashtra, India`
- `[EMAIL]` `hingnetare@gmail.com`

### P5
**Correctly detected (TP):**
- `[DOB]` `15 March 1970`

### P6
**Correctly detected (TP):**
- `[DOB]` `12/05/1968`

### P7
**Correctly detected (TP):**
- `[IP_ADDRESS]` `192.168.1.100`

### SYN1 *(synthetic)*
**Correctly detected (TP):**
- `[SSN]` `523-45-6789`

### SYN2 *(synthetic)*
**Correctly detected (TP):**
- `[CREDIT_CARD]` `4539 1488 0343 6467`

### SYN3 *(synthetic)*
**Correctly detected (TP):**
- `[CREDIT_CARD]` `4111111111111111`

---

*Generated automatically by `evaluation/evaluate.py`. No numbers were fabricated — every figure derives from running `detect_all_pii` against `ground_truth.json`.*
