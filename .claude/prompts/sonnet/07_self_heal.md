# Sonnet Prompt: Self-Healing Investigation

**Version:** 1
**Purpose:** When Haiku scraping fails, Sonnet investigates and fixes the reference
**Deployed by:** Case (Opus) — triggered when source_catalog.consecutive_failures >= 3
**Output:** Diagnosis and fix (new URL, updated format, or escalation to human)

---

## Prompt

```
A scraping source for {STATE_NAME} ({STATE_CODE}) has failed 3 consecutive times. Investigate and fix.

### Failed Source
- **Name:** {SOURCE_NAME}
- **URL:** {SOURCE_URL}
- **Type:** {SOURCE_TYPE}
- **Expected Format:** {EXPECTED_FORMAT}
- **Last Successful Scrape:** {LAST_SUCCESS_DATE}
- **Error Details:** {ERROR_DETAILS_FROM_SCRAPE_LOGS}

### Your Investigation Steps

1. **Try the URL** — does it load at all? What HTTP status?
2. **If 404/gone:** Search for the new URL. Check:
   - The agency's main website for updated links
   - Web search for "{STATE_NAME} fish stocking reports {YEAR}"
   - Internet Archive / Wayback Machine for redirect history
3. **If it loads but format changed:**
   - Describe what changed (new HTML structure, different table format, moved to PDF, etc.)
   - Provide the new format details so the prompt template can be updated
4. **If access blocked:**
   - Is it a CAPTCHA? Rate limit? Login wall?
   - Is there an alternative URL or API that provides the same data?
5. **If the data source is genuinely gone:**
   - Is there a replacement source from the same agency?
   - Is there an alternative source (different agency, federal source, etc.)?

### Output Format

```json
{
  "source_name": "{SOURCE_NAME}",
  "original_url": "{SOURCE_URL}",
  "diagnosis": "url_moved | format_changed | access_blocked | source_removed | temporary_outage",
  "details": "The stocking page moved to a new URL as part of a site redesign.",
  "fix": {
    "action": "update_url | update_prompt | add_alternative | mark_retired | wait_and_retry",
    "new_url": "https://new-url-if-applicable.gov/stocking",
    "new_format": "html_table",
    "new_format_details": "Table now has 6 columns instead of 5, added 'length' column",
    "prompt_changes_needed": "Add 'average_length' field to extraction schema",
    "alternative_source": null
  },
  "confidence": 0.9,
  "escalate_to_human": false,
  "notes": "Found via redirect chain on agency website. New URL confirmed active."
}
```

### Decision Tree

```
URL loads?
├── YES → Format same?
│   ├── YES → Temporary outage. Reset failure counter. Wait and retry.
│   └── NO  → Format changed. Document changes. Update prompt template.
└── NO  → URL moved?
    ├── YES → Find new URL. Update reference. Test.
    └── NO  → Source removed?
        ├── YES → Find alternative. Or mark retired.
        └── UNCLEAR → Escalate to human.
```

### Critical Rules

1. **Find the fix, don't just report the problem.** Your job is to resolve this.
2. **Verify your fix actually works** — if you find a new URL, confirm it has the data we need.
3. **If you can't fix it, escalate clearly** — explain exactly what's wrong and what you tried.
4. **Don't guess URLs.** Only provide URLs you've verified.
```

---

## Success Criteria

- [ ] Root cause identified
- [ ] Fix provided or escalation with clear reasoning
- [ ] New URLs verified active
- [ ] Prompt changes documented if format changed

## Known Pitfalls (update after each state)

- {will be populated as we learn}
