# State Onboarding: {STATE_NAME} ({STATE_CODE})

**Started:** {date}
**Status:** BIBLE | SOURCES | DATA_LAYER | TESTING | CERTIFIED
**Certified:** —

---

## Phase 1: Bible Foundation

### OSM (lakes/reservoirs/ponds)
- [ ] `python3 pipeline/osm.py {STATE}` — download OSM water features
- [ ] `python3 -m pipeline.osm_migrate --state {STATE}` — dry run, review
- [ ] `python3 -m pipeline.osm_migrate --state {STATE} --apply` — insert
- **Standing water imported:** 0

### USGS (river gauges)
- [ ] `python3 -m pipeline.usgs_rivers --state {STATE}` — dry run, review
- [ ] `python3 -m pipeline.usgs_rivers --state {STATE} --apply` — insert
- **River entries created:** 0
- **Gauges wired:** 0

### GNIS (county backfill)
- [ ] `python3 -m pipeline.enrich_gnis --state {STATE} --apply`
- **Counties backfilled:** 0

### Bible Totals
- **Total water bodies:** 0
- **OSM sourced:** 0
- **USGS sourced:** 0

---

## Phase 2: Source Discovery
- [ ] State DWR/DNR stocking report found
- [ ] Regulations source found
- [ ] All sources documented in `sources.md`
- [ ] All URLs verified active

---

## Phase 3: Data Layer
- [ ] NOAA weather wired and fetched
- [ ] USGS conditions flowing
- [ ] Stocking events imported
- [ ] Species data populated
- **Stocking events:** 0
- **Weather forecasts:** 0
- **Conditions readings:** 0

---

## Phase 4: Prompt Engineering
- [ ] Stocking prompt v1 written and tested
- [ ] Accuracy >90%
- **Prompt version:** —
- **Accuracy:** —

---

## Phase 5: Certification
- [ ] All phases complete
- [ ] Pipeline ran 3x without intervention
- [ ] Match rate >95%

---

## Notes

{running notes, issues, decisions}
