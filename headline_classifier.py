#!/usr/bin/env python3
"""CLI tool that classifies financial news headlines as Bullish, Bearish, or Neutral using the Gemini API."""

import argparse
import csv
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

MODEL = "gemini-3.5-flash-lite"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
OUTPUT_CSV = "classifications_output.csv"

SYSTEM_PROMPT = (
    "You are a financial sentiment classifier. Given a financial news headline, "
    "classify its market sentiment as exactly one of: Bullish, Bearish, or Neutral. "
    "Then give a one-sentence reason for the classification.\n\n"
    "Respond in exactly this format, with no extra text:\n"
    "Classification: <Bullish|Bearish|Neutral>\n"
    "Reason: <one sentence>"
)

SAMPLE_HEADLINES = [
    "Nvidia shares surge 8% after blowout earnings beat Wall Street estimates",
    "Fed signals three rate cuts in 2026 as inflation cools toward 2% target",
    "Boeing stock plunges following fresh reports of production defects",
    "Apple beats on revenue but misses iPhone sales expectations for third straight quarter",
    "US job growth slows sharply, raising fears of a looming recession",
    "Oil prices climb as OPEC+ announces surprise production cuts",
    "Tesla recalls 2 million vehicles over autopilot safety concerns",
    "Retail sales data comes in flat, matching economist forecasts exactly",
    "JPMorgan raises full-year profit guidance on strong trading revenue",
    "Treasury yields spike after hotter-than-expected CPI report",
    "Amazon announces 15,000 layoffs amid cost-cutting push in cloud division",
    "Microsoft and OpenAI expand partnership with new $10 billion investment",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classify financial news headlines as Bullish, Bearish, or Neutral."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default=None,
        help="Optional path to a CSV file containing a 'headline' column. "
        "If omitted, a built-in sample dataset is used.",
    )
    return parser.parse_args()


def load_headlines(csv_path):
    if csv_path is None:
        return list(SAMPLE_HEADLINES)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "headline" not in (reader.fieldnames or []):
            print(
                f"Error: CSV file must have a 'headline' column. Found: {reader.fieldnames}",
                file=sys.stderr,
            )
            sys.exit(1)
        return [row["headline"].strip() for row in reader if row.get("headline", "").strip()]


def parse_classification(text):
    classification = "Neutral"
    reason = "No reason provided."
    for line in text.strip().splitlines():
        line = line.strip()
        if line.lower().startswith("classification:"):
            value = line.split(":", 1)[1].strip()
            if value in ("Bullish", "Bearish", "Neutral"):
                classification = value
        elif line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()
    return classification, reason


RETRYABLE_CODES = {408, 429, 500, 502, 503, 504}


def classify_headline(client, headline):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            interaction = client.interactions.create(
                model=MODEL,
                system_instruction=SYSTEM_PROMPT,
                input=headline,
                generation_config={"max_output_tokens": 150},
            )
            return parse_classification(interaction.output_text or "")
        except errors.APIError as e:
            last_error = e
            if e.code not in RETRYABLE_CODES:
                break
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
    print(f"Error classifying headline after {MAX_RETRIES} attempts: {last_error}", file=sys.stderr)
    return "Error", f"API call failed: {last_error}"


def print_table(results):
    headline_width = min(max((len(r[0]) for r in results), default=8), 60)
    class_width = max((len(r[1]) for r in results), default=14)

    def fmt(headline, classification, reason):
        h = (headline[: headline_width - 1] + "…") if len(headline) > headline_width else headline
        return f"{h:<{headline_width}} | {classification:<{class_width}} | {reason}"

    print(fmt("Headline", "Classification", "Reason"))
    print("-" * (headline_width + class_width + len("Reason") + 6))
    for headline, classification, reason in results:
        print(fmt(headline, classification, reason))


def write_csv(results, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Headline", "Classification", "Reason"])
        writer.writerows(results)


def main():
    load_dotenv()
    args = parse_args()
    headlines = load_headlines(args.csv_file)

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY is not set.", file=sys.stderr)
        print("Copy .env.example to .env and add your API key.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client()

    results = []
    for headline in headlines:
        classification, reason = classify_headline(client, headline)
        results.append((headline, classification, reason))

    print_table(results)
    write_csv(results, OUTPUT_CSV)
    print(f"\nSaved {len(results)} classifications to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
