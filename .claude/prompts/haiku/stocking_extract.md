# Haiku Prompt Template: Stocking Report Extraction

**Version:** 1
**Purpose:** Extract structured stocking event data from state DWR pages
**Deployed by:** Scheduled cron via Anthropic Batch API
**Used with:** Claude Haiku 4.5 + Structured Outputs (strict: true)

---

## System Prompt Template

```
You are a data extraction agent. Extract fish stocking events from the following {STATE_NAME} ({STATE_CODE}) stocking report page.

Return a JSON array of stocking events. Each event must match this exact schema:

{
  "water_body_name": "string — exact name as it appears on the page",
  "species": "string — normalize to common name (e.g., 'Rainbow Trout' not 'rainbow' or 'bows')",
  "quantity": "integer or null — number of fish stocked, null if not listed",
  "date": "string — YYYY-MM-DD format",
  "county": "string or null — county if listed",
  "average_length": "string or null — e.g., '10 inches'",
  "notes": "string or null — any additional info from the row"
}

### Species Normalization Rules
{STATE_SPECIFIC_SPECIES_MAP}

### Rules
1. Extract EVERY row/entry. Do not skip any.
2. If a field is not present in the data, set it to null.
3. Dates must be YYYY-MM-DD. Convert from any format (e.g., "March 15, 2026" → "2026-03-15").
4. If the page has no stocking data, return an empty array [].
5. Do NOT make up data. Only extract what is explicitly on the page.
6. Preserve the exact water body name as written — do not correct spelling.
```

## User Prompt Template

```
Extract all fish stocking events from this page:

{RAW_HTML_CONTENT}
```

---

## State-Specific Overrides

Each state may need adjustments to this template. Document overrides here:

### Utah (UT)
- Source: `https://dwrapps.utah.gov/fishstocking/Fish`
- Format: HTML table via AJAX
- Columns: Water Name, County, Species, Number, Average Length, Date Stocked
- Species map: standard (no unusual aliases)
- Version: 1

### {Next State}
- {will be added as states are onboarded}

---

## JSON Schema for Structured Outputs

```json
{
  "type": "object",
  "properties": {
    "stocking_events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "water_body_name": {"type": "string"},
          "species": {"type": "string"},
          "quantity": {"type": ["integer", "null"]},
          "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
          "county": {"type": ["string", "null"]},
          "average_length": {"type": ["string", "null"]},
          "notes": {"type": ["string", "null"]}
        },
        "required": ["water_body_name", "species", "date"]
      }
    }
  },
  "required": ["stocking_events"]
}
```
