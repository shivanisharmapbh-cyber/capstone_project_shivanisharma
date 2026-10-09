"""Generate and validate a business narrative from verified findings."""

import calendar
import json
import os
from pathlib import Path


def month_name(value):
    """Convert a YYYY-MM value to an English month name."""
    return calendar.month_name[int(value.split("-")[1])]


def check_numeric_accuracy(narrative, findings):
    """Print a result for each required figure and assert accuracy."""
    text = narrative.replace(",", "").lower()

    def contains_number(value):
        # Accept both fixed decimals and omitted trailing zeros.
        return (
            f"{value:.2f}" in text
            or f"{value:g}" in text
        )

    peak = findings["true_peak_month"]

    checks = {
        "Cleaned total revenue": contains_number(
            findings["cleaned_total_revenue_inr"]
        ),
        "COD return rate": contains_number(
            findings["return_rate_by_payment"]["COD"]
        ),
        "Highest-risk segment return rate": contains_number(
            findings["highest_risk_segment"]["return_rate_pct"]
        ),
        "Duplicate reconciliation delta": contains_number(
            findings["duplicate_reconciliation_delta_inr"]
        ),
        "Peak month and revenue": (
            month_name(peak["month"]).lower() in text
            and contains_number(peak["revenue_inr"])
        ),
    }

    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} — {label}")

    assert all(checks.values()), "Required narrative figures are missing."
    return True


def generate_scr_narrative_offline(findings: dict) -> dict:
    """Create a deterministic narrative without a key or network."""
    try:
        rates = findings["return_rate_by_payment"]
        risk = findings["highest_risk_segment"]
        peak = findings["true_peak_month"]
        inflated = findings["outlier_inflated_month"]

        narrative = (
            "Situation\n"
            f"Cleaned revenue is "
            f"₹{findings['cleaned_total_revenue_inr']:,.2f}, compared with "
            f"raw revenue of ₹{findings['raw_total_revenue_inr']:,.2f}. "
            f"The duplicate-driven reconciliation difference is "
            f"₹{findings['duplicate_reconciliation_delta_inr']:,.2f}. "
            "The cleaned total provides a consistent basis for operational "
            "and financial reporting after duplicate removal.\n\n"

            "Complication\n"
            f"COD has a return rate of {rates['COD']:.1f}%, compared with "
            f"{rates['CARD']:.1f}% for Card and {rates['UPI']:.1f}% for UPI. "
            f"The highest-risk segment is {risk['payment_method']} in "
            f"Tier-{risk['city_tier']} cities, with a return rate of "
            f"{risk['return_rate_pct']:.1f}%. "
            f"{month_name(inflated['month'])}'s apparent revenue of "
            f"₹{inflated['apparent_revenue_inr']:,.2f} falls to "
            f"₹{inflated['corrected_revenue_inr']:,.2f} when quantity "
            "outliers are excluded. Bulk orders therefore distort "
            "the apparent monthly revenue pattern.\n\n"

            "Resolution\n"
            f"Use {month_name(peak['month'])}, with outlier-corrected "
            f"revenue of ₹{peak['revenue_inr']:,.2f}, as the actual peak "
            "month in the corrected series. Prioritize investigation of "
            "COD returns in the highest-risk city tier. Review delivery "
            "confirmation and return reasons before selecting an "
            "intervention. Report bulk-order revenue separately from the "
            "corrected trend, and retain the duplicate reconciliation "
            "alongside financial summaries. These are proposed actions; "
            "the supplied findings do not establish causes of returns "
            "or quantify the benefits of an intervention."
        )

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": 0,
            "source": "offline",
        }

    except Exception as err:
        return {
            "status": "error",
            "narrative": None,
            "message": str(err),
        }


def _call_gemini(findings: dict, api_key: str) -> dict:
    """Return a structured result even when the API request fails."""
    try:
        # Import only for online use; offline use needs no SDK installation.
        from google import genai
        from google.genai import types

        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's "
            "regional ops and finance heads. Write approximately "
            "250 words in three labeled sections: Situation, "
            "Complication, Resolution. Every number in the output "
            "must come from the supplied findings and appear with "
            "the same value. Do not invent statistics, calculate new "
            "ratios, or give numerical targets. Formatting commas and "
            "trailing zeros is allowed. Translate month dates into "
            "English month names. Include the cleaned revenue, raw "
            "revenue, duplicate reconciliation delta, payment return "
            "rates, highest-risk segment, true peak month and revenue, "
            "and the inflated month's apparent and corrected revenue. "
            "Describe recommendations as proposed actions, not proven "
            "causes or guaranteed outcomes. Do not number the sections."
        )

        contents = (
            "Write the SCR business narrative using these verified "
            "findings:\n"
            + json.dumps(findings, indent=2, ensure_ascii=False)
        )

        with genai.Client(
            api_key=api_key,
            # The SDK measures timeout in milliseconds: 60 seconds.
            http_options=types.HttpOptions(timeout=60000),
        ) as client:
            response = client.models.generate_content(
                model=os.environ.get(
                    "GEMINI_MODEL", "gemini-3.5-flash-lite"
                ),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    # Minimize randomness for a factual business report.
                    # Temperature zero does not guarantee identical API text.
                    temperature=0.0,
                    max_output_tokens=2048,
                ),
            )

        narrative = response.text
        if not narrative:
            raise ValueError("Gemini returned no narrative text.")

        check_numeric_accuracy(narrative, findings)

        usage = response.usage_metadata

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": usage.total_token_count if usage else None,
            "source": "gemini",
        }

    except Exception as err:
        return {
            "status": "error",
            "narrative": None,
            "message": str(err),
        }


def generate_scr_narrative(findings: dict) -> dict:
    """Use Gemini when configured, otherwise use the offline fallback."""
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if api_key:
        result = _call_gemini(findings, api_key)

        if result["status"] == "success":
            return result

        fallback = generate_scr_narrative_offline(findings)
        fallback["fallback_reason"] = result["message"]
        return fallback

    return generate_scr_narrative_offline(findings)


def main():
    narrator_dir = Path(__file__).resolve().parent
    findings_path = narrator_dir / "findings.json"

    with findings_path.open(encoding="utf-8") as file:
        findings = json.load(file)

    result = generate_scr_narrative(findings)

    if result["status"] == "error":
        print(f"Narrative generation failed: {result['message']}")
        return

    print(f"Generation source: {result['source']}")
    print(f"Tokens: {result['tokens']}")

    if "fallback_reason" in result:
        print(f"Fallback reason: {result['fallback_reason']}")

    print("\n" + result["narrative"])

    # Preserve online evidence separately from offline output.
    filename = (
        "sample_output.txt"
        if result["source"] == "gemini"
        else "sample_output_offline.txt"
    )

    output_path = narrator_dir / filename
    output_path.write_text(result["narrative"], encoding="utf-8")

    # Validate the actual saved text.
    saved_text = output_path.read_text(encoding="utf-8")
    print("\nNumeric accuracy checks on saved output:")
    check_numeric_accuracy(saved_text, findings)

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
