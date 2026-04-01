# Sonnet Prompt: Reference Verification

**Version:** 1
**Purpose:** Verify that every URL/reference in the system is live, active, and returns expected data
**Deployed by:** Case (Opus) — on initial onboarding and periodic audits
**Output:** Verification report with status per reference

---

## Prompt

```
You are auditing data source references for {STATE_NAME} ({STATE_CODE}) in FishOn.

### References to Verify
{PASTE_SOURCE_CATALOG_AND_DATA_SOURCE_LINKS}

### For Each Reference:

1. **Hit the URL** — does it load? What HTTP status?
2. **Check the content** — does it contain fishing/stocking data as expected?
3. **Check the format** — is it still the same format (HTML table, PDF, etc.) we expect?
4. **Check freshness** — when was the data last updated? Is the source still being maintained?
5. **Check access** — any new login walls, CAPTCHAs, or rate limiting?

### Output Format

```json
[
  {
    "source_name": "Utah DWR Stocking Reports",
    "url": "https://dwrapps.utah.gov/fishstocking/Fish",
    "status": "active",
    "http_status": 200,
    "format_matches": true,
    "format": "html_table",
    "last_data_update": "2026-03-15",
    "access_issues": "none",
    "notes": "Working as expected",
    "verified_date": "2026-03-18"
  },
  {
    "source_name": "Utah Fishing Guidebook PDF",
    "url": "https://wildlife.utah.gov/fishing-guidebook.html",
    "status": "changed",
    "http_status": 200,
    "format_matches": false,
    "format": "was pdf, now html",
    "last_data_update": "2026-01-01",
    "access_issues": "none",
    "notes": "Format changed from PDF to HTML page. Prompt template needs update.",
    "verified_date": "2026-03-18"
  }
]
```

### Status Values
- **active**: URL loads, data present, format matches expectations
- **changed**: URL loads but format/structure changed — needs prompt update
- **moved**: URL redirects to a new location — update the reference
- **broken**: URL returns error (404, 500, timeout) — needs investigation
- **blocked**: Access denied, login wall, CAPTCHA — needs alternative approach
- **stale**: URL loads but data hasn't been updated in >90 days — may be abandoned

### Critical Rules

1. **Every reference gets checked.** No skipping.
2. **Record the exact date of verification.**
3. **If a URL redirects, note both the old and new URL.**
4. **If the format changed, describe what changed specifically** so the prompt template can be updated.
```

---

## Success Criteria

- [ ] Every reference has a verification status
- [ ] Broken/changed references flagged with actionable notes
- [ ] Verification dates recorded
- [ ] No false "active" statuses — actually confirm content matches

## Known Pitfalls (update after each state)

- {will be populated as we learn}
