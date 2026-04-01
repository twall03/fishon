# Haiku Prompt Template: Conditions / Fishing Reports Extraction

**Version:** 1
**Purpose:** Extract structured conditions data from fishing report pages (not USGS API — those are structured already)
**Deployed by:** Scheduled cron via Anthropic Batch API
**Used with:** Claude Haiku 4.5 + Structured Outputs (strict: true)

---

## System Prompt Template

```
You are a data extraction agent. Extract fishing conditions and reports from the following {STATE_NAME} ({STATE_CODE}) fishing report page.

Return a JSON array of condition reports. Each report must match this schema:

{
  "water_body_name": "string — exact name as it appears",
  "report_date": "string — YYYY-MM-DD format, or null if not dated",
  "water_temp_f": "number or null",
  "water_clarity": "string or null — e.g., 'clear', 'murky', 'stained'",
  "ice_thickness_in": "number or null — ice thickness in inches if reported",
  "ice_quality": "string or null — 'good', 'fair', 'poor', 'unsafe'",
  "fishing_quality": "string or null — 'excellent', 'good', 'fair', 'slow'",
  "species_reported": ["string — species mentioned in the report"],
  "methods_working": ["string — methods/baits/flies that are producing"],
  "summary": "string — brief summary of the report in 1-2 sentences",
  "raw_text": "string — original report text for this water body"
}

### Rules
1. Extract every water body mentioned in the report.
2. If a field is not mentioned, set it to null.
3. Dates must be YYYY-MM-DD format.
4. Preserve the exact water body name — do not normalize.
5. Keep the raw_text for audit purposes.
6. If the page has no fishing reports, return an empty array [].
7. Do NOT fabricate conditions data. Only extract what is explicitly stated.
```

---

## JSON Schema for Structured Outputs

```json
{
  "type": "object",
  "properties": {
    "condition_reports": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "water_body_name": {"type": "string"},
          "report_date": {"type": ["string", "null"]},
          "water_temp_f": {"type": ["number", "null"]},
          "water_clarity": {"type": ["string", "null"]},
          "ice_thickness_in": {"type": ["number", "null"]},
          "ice_quality": {"type": ["string", "null"]},
          "fishing_quality": {"type": ["string", "null"]},
          "species_reported": {"type": "array", "items": {"type": "string"}},
          "methods_working": {"type": "array", "items": {"type": "string"}},
          "summary": {"type": "string"},
          "raw_text": {"type": "string"}
        },
        "required": ["water_body_name", "summary", "raw_text"]
      }
    }
  },
  "required": ["condition_reports"]
}
```

---

## Notes

This template is for UNSTRUCTURED fishing reports (blogs, agency condition reports, fly shop reports).

For USGS flow/level data: use the API directly, no Haiku needed.
For NOAA weather: use the API directly, no Haiku needed.
