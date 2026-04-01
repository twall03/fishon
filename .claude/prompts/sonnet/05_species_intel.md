# Sonnet Prompt: Species Intelligence Per Water Body

**Version:** 1
**Purpose:** Populate water_body_species with what lives in each water and how to catch it
**Deployed by:** Case (Opus)
**Output:** Structured JSON for water_body_species table import

---

## Prompt

```
You have the water body bible for {STATE_NAME} ({STATE_CODE}). For each water body, research what species are present and how anglers catch them at that specific location.

### Water Body Bible
{PASTE_WATER_BODY_LIST}

### Canonical Species List
Rainbow Trout, Brown Trout, Brook Trout, Cutthroat Trout, Lake Trout, Tiger Trout, Splake, Golden Trout, Bonneville Cutthroat Trout, Bear Lake Cutthroat Trout, Kokanee Salmon, Chinook Salmon, Atlantic Salmon, Largemouth Bass, Smallmouth Bass, Striped Bass, White Bass, Wiper, Walleye, Sauger, Yellow Perch, Bluegill, Green Sunfish, Black Crappie, White Crappie, Channel Catfish, Blue Catfish, Flathead Catfish, Northern Pike, Tiger Muskie, Muskellunge, Mountain Whitefish, Bonneville Cisco, Common Carp, Grass Carp

### For Each Water Body × Species Combination

Only include species that are ACTUALLY present in the water body. Sources:
- Stocking reports (confirmed stocked species)
- State fishing guide (listed species)
- Regulations (species mentioned in special rules)
- General knowledge for well-known fisheries

For each combination, provide what you can:

```json
{
  "water_body_name": "Strawberry Reservoir",
  "species": "Rainbow Trout",
  "is_stocked": true,
  "is_native": false,
  "abundance": "abundant",
  "popular_methods": ["bait", "trolling", "fly fishing", "ice fishing"],
  "popular_baits": ["PowerBait", "worm", "marshmallow"],
  "popular_lures": ["kastmaster", "jake's spin-a-lure", "wedding ring"],
  "popular_flies": ["woolly bugger", "chironomid", "leech"],
  "best_season": "spring",
  "best_time": "early morning",
  "size_range": "12-20 inches",
  "record_size": null,
  "tips": "Fish the inlet in spring when flows are high. Trolling the dam works year-round.",
  "regulations": "4 fish limit, no size restriction",
  "data_source": "utah_dwr, general_knowledge",
  "confidence": 0.8
}
```

### Confidence Scale
- **1.0**: Confirmed from state agency data (stocking report, fishing guide)
- **0.8**: Well-known fishery, high confidence from multiple sources
- **0.6**: Likely accurate based on regional knowledge
- **0.4**: Best guess — should be verified

### Critical Rules

1. **Only include species actually present.** Don't add Largemouth Bass to a high-elevation trout lake just to fill the table.
2. **"Unknown" is fine.** If you don't know the popular methods for a small creek, leave those fields null. Partial data > wrong data.
3. **Use canonical species names** from the list above. Don't add "Rainbows" — use "Rainbow Trout".
4. **Location-specific tips are gold.** "Fish the inlet" is better than "use PowerBait." If you don't have location-specific info, leave tips null.
5. **Stocking data = is_stocked: true.** If a species appears in stocking reports for this water, it's stocked.
6. **Set confidence honestly.** Don't claim 1.0 for general knowledge.
```

---

## Success Criteria

- [ ] Every water body has at least 1 species entry
- [ ] Stocked species marked as is_stocked: true
- [ ] Confidence scores are honest, not inflated
- [ ] Popular methods/baits only included when actually known
- [ ] No fabricated species-water combinations

## Known Pitfalls (update after each state)

- {will be populated as we learn}
