# Headline Classifier

A Python CLI tool that classifies financial news headlines as **Bullish**, **Bearish**, or **Neutral** using the Google Gemini API (`gemini-3.5-flash-lite`), with a one-sentence reason for each classification.

## What it does

- Sends each headline to Gemini with a system instruction to classify sentiment as exactly one of `Bullish`, `Bearish`, or `Neutral`, plus a one-sentence reason.
- Prints a formatted table to the terminal: `Headline | Classification | Reason`.
- Saves all results to `classifications_output.csv`.
- Retries automatically (up to 3 attempts) on transient API errors (rate limits, connection issues, server errors).

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your Gemini API key (from [Google AI Studio](https://aistudio.google.com/apikey)):

   ```bash
   cp .env.example .env
   # then edit .env and set GEMINI_API_KEY=AIza...
   ```

## Usage

Run with the built-in sample dataset (12 headlines covering stocks, Fed policy, earnings, and macro news):

```bash
python headline_classifier.py
```

Run against your own headlines from a CSV file (must have a `headline` column):

```bash
python headline_classifier.py my_headlines.csv
```

Example input CSV:

```csv
headline
Nvidia shares surge 8% after blowout earnings beat Wall Street estimates
Fed signals three rate cuts in 2026 as inflation cools toward 2% target
```

## Example output

```
Headline                                                     | Classification | Reason
---------------------------------------------------------------------------------------
Nvidia shares surge 8% after blowout earnings beat Wall St…  | Bullish        | The stock jumped sharply on earnings that exceeded analyst expectations.
Fed signals three rate cuts in 2026 as inflation cools tow…  | Bullish        | Rate cuts and cooling inflation are generally supportive of risk assets.
Boeing stock plunges following fresh reports of production…  | Bearish        | Safety and production issues are weighing heavily on the stock.
Retail sales data comes in flat, matching economist forecas…  | Neutral        | The data matched expectations with no clear directional surprise.

Saved 12 classifications to classifications_output.csv
```

Results are also written to `classifications_output.csv` with columns `Headline, Classification, Reason`.

## Model

Uses `gemini-3.5-flash-lite`, Google's fastest and most cost-effective model, well suited to a lightweight classification task like this.
