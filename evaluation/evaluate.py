"""
evaluate.py
-----------
Evaluates detect_all_pii against the hand-labeled ground_truth.json.

Accuracy definition used here:
    accuracy = TP / (TP + FP + FN)

This is the Jaccard / intersection-over-union style accuracy for span
detection.  Standard multi-class accuracy (with true negatives) does not
map cleanly onto this task because there is no fixed set of negative
examples — the "universe" of non-PII text is effectively unbounded.

Run from the project root:
    python evaluation/evaluate.py
"""

import json
import os
import sys
import io

# Always write UTF-8 to stdout so the report chars survive any terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import spacy
from detectors import detect_all_pii

GROUND_TRUTH_FILE = os.path.join(os.path.dirname(__file__), "ground_truth.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "evaluation_report.md")


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

def load_ground_truth(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# EVALUATE ONE RECORD
# ============================================================

def evaluate_record(record: dict, nlp) -> dict:
    """
    Run detect_all_pii on the text snippet and match detections to
    expected PII spans by exact (type, value) match.

    Returns a dict with:
        tp_pairs  – list of (type, value) correctly detected
        fp_pairs  – list of (type, value) detected but not in ground truth
        fn_pairs  – list of (type, value) in ground truth but not detected
    """
    text = record["text_snippet"]
    expected = {(e["type"], e["value"]) for e in record["expected"]}

    detections = detect_all_pii(text, nlp)
    detected = {(d["type"], d["value"]) for d in detections}

    tp = expected & detected
    fp = detected - expected
    fn = expected - detected

    return {
        "id": record.get("id", "?"),
        "synthetic": record.get("synthetic", False),
        "tp_pairs": list(tp),
        "fp_pairs": list(fp),
        "fn_pairs": list(fn),
    }


# ============================================================
# AGGREGATE METRICS
# ============================================================

def compute_metrics(results: list[dict]) -> dict:
    """
    Aggregate per-type and overall precision / recall / F1 / accuracy.

    Accuracy definition:  TP / (TP + FP + FN)
    """
    per_type: dict[str, dict[str, int]] = {}

    global_tp = 0
    global_fp = 0
    global_fn = 0

    for r in results:
        for pii_type, _ in r["tp_pairs"]:
            per_type.setdefault(pii_type, {"tp": 0, "fp": 0, "fn": 0})
            per_type[pii_type]["tp"] += 1
            global_tp += 1

        for pii_type, _ in r["fp_pairs"]:
            per_type.setdefault(pii_type, {"tp": 0, "fp": 0, "fn": 0})
            per_type[pii_type]["fp"] += 1
            global_fp += 1

        for pii_type, _ in r["fn_pairs"]:
            per_type.setdefault(pii_type, {"tp": 0, "fp": 0, "fn": 0})
            per_type[pii_type]["fn"] += 1
            global_fn += 1

    def _metrics(tp, fp, fn):
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        accuracy  = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
        return {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
        }

    type_metrics = {
        t: _metrics(**counts)
        for t, counts in sorted(per_type.items())
    }

    overall = _metrics(global_tp, global_fp, global_fn)

    return {"per_type": type_metrics, "overall": overall}


# ============================================================
# FORMAT REPORT
# ============================================================

def format_report(results: list[dict], metrics: dict) -> str:
    lines = []

    lines.append("# PII Detection Evaluation Report")
    lines.append("")
    lines.append(
        "> **Accuracy definition**: `TP / (TP + FP + FN)` — the Jaccard/IoU metric for "
        "span detection. Standard accuracy (with true negatives) does not apply here "
        "because the universe of non-PII text is effectively unbounded and there is no "
        "fixed set of negative examples."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Per-type table ----
    lines.append("## Per-Type Metrics")
    lines.append("")
    lines.append(
        "| PII Type       | TP | FP | FN | Precision | Recall |   F1   | Accuracy |"
    )
    lines.append(
        "|----------------|----|----|----|-----------|--------|--------|----------|"
    )

    for pii_type, m in metrics["per_type"].items():
        lines.append(
            f"| {pii_type:<14} "
            f"| {m['tp']:>2} "
            f"| {m['fp']:>2} "
            f"| {m['fn']:>2} "
            f"| {m['precision']:>9.2%} "
            f"| {m['recall']:>6.2%} "
            f"| {m['f1']:>6.2%} "
            f"| {m['accuracy']:>8.2%} |"
        )

    lines.append("")

    # ---- Overall row ----
    lines.append("## Overall Metrics")
    lines.append("")
    ov = metrics["overall"]
    lines.append(
        "| Metric    | Value    |"
    )
    lines.append(
        "|-----------|----------|"
    )
    lines.append(f"| TP        | {ov['tp']:>8} |")
    lines.append(f"| FP        | {ov['fp']:>8} |")
    lines.append(f"| FN        | {ov['fn']:>8} |")
    lines.append(f"| Precision | {ov['precision']:>8.2%} |")
    lines.append(f"| Recall    | {ov['recall']:>8.2%} |")
    lines.append(f"| F1        | {ov['f1']:>8.2%} |")
    lines.append(f"| Accuracy  | {ov['accuracy']:>8.2%} |")
    lines.append("")

    # ---- Per-record breakdown ----
    lines.append("---")
    lines.append("")
    lines.append("## Per-Record Breakdown")
    lines.append("")

    for r in results:
        synth_tag = " *(synthetic)*" if r["synthetic"] else ""
        lines.append(f"### {r['id']}{synth_tag}")

        if r["tp_pairs"]:
            lines.append("**Correctly detected (TP):**")
            for t, v in sorted(r["tp_pairs"]):
                lines.append(f"- `[{t}]` `{v}`")

        if r["fp_pairs"]:
            lines.append("")
            lines.append("**False positives (FP):**")
            for t, v in sorted(r["fp_pairs"]):
                lines.append(f"- `[{t}]` `{v}`")

        if r["fn_pairs"]:
            lines.append("")
            lines.append("**Missed (FN):**")
            for t, v in sorted(r["fn_pairs"]):
                lines.append(f"- `[{t}]` `{v}`")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*Generated automatically by `evaluation/evaluate.py`. "
        "No numbers were fabricated — every figure derives from running "
        "`detect_all_pii` against `ground_truth.json`.*"
    )
    lines.append("")

    return "\n".join(lines)


# ============================================================
# PRINT CONSOLE TABLE
# ============================================================

def print_console_table(metrics: dict):
    sep = "-" * 80
    print(sep)
    print(
        f"{'PII TYPE':<14}  {'TP':>3}  {'FP':>3}  {'FN':>3}  "
        f"{'PREC':>7}  {'REC':>7}  {'F1':>7}  {'ACC':>7}"
    )
    print(sep)

    for pii_type, m in metrics["per_type"].items():
        print(
            f"{pii_type:<14}  {m['tp']:>3}  {m['fp']:>3}  {m['fn']:>3}  "
            f"{m['precision']:>7.2%}  {m['recall']:>7.2%}  "
            f"{m['f1']:>7.2%}  {m['accuracy']:>7.2%}"
        )

    print(sep)
    ov = metrics["overall"]
    print(
        f"{'OVERALL':<14}  {ov['tp']:>3}  {ov['fp']:>3}  {ov['fn']:>3}  "
        f"{ov['precision']:>7.2%}  {ov['recall']:>7.2%}  "
        f"{ov['f1']:>7.2%}  {ov['accuracy']:>7.2%}"
    )
    print(sep)


# ============================================================
# MAIN
# ============================================================

def main():
    print("Loading spaCy model …")
    nlp = spacy.load("en_core_web_sm")

    print("Loading ground truth …")
    records = load_ground_truth(GROUND_TRUTH_FILE)

    print(f"Evaluating {len(records)} records …")
    results = [evaluate_record(r, nlp) for r in records]

    metrics = compute_metrics(results)

    print("\nEVALUATION RESULTS")
    print_console_table(metrics)

    report_text = format_report(results, metrics)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
