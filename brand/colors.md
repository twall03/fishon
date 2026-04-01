# Fishon Brand Guide

## Brand Name
**fishon** — lowercase, one word. Logo reads **FISHON** in uppercase DM Sans 700, letter-spacing 2px.

## Tagline
"All your water. One app."

---

## Color Palette

### Primary

| Name        | Hex       | RGB             | Usage                                        |
|-------------|-----------|-----------------|----------------------------------------------|
| Warm Tan    | `#EDE8E0` | 237, 232, 224   | Body background, content sections, cards     |
| Dark Brown  | `#3D3528` | 61, 53, 40      | Nav, hero, map section, footer, heading text |
| Mid Brown   | `#7A7060` | 122, 112, 96    | Body text, descriptions, paragraphs          |
| Light Brown | `#A09888` | 160, 152, 136   | Labels, captions, dim/tertiary text          |
| Border Tan  | `#D5CEC2` | 213, 206, 194   | Dividers, card borders, separators           |

### Accent

| Name        | Hex       | RGB             | Usage                                              |
|-------------|-----------|-----------------|-----------------------------------------------------|
| Water Blue  | `#2E9BCC` | 46, 155, 204    | Primary accent — CTAs, logo fish, links, stat numbers, section labels, active states, pricing highlights |
| Blue Hover  | `#2589B8` | 37, 137, 184    | Button hover states                                |
| Pine Green  | `#2D6B3F` | 45, 107, 63     | Secondary — stocking badges, alternating feature icons, checkmarks |

### Functional

| Token          | Value                      | Usage                    |
|----------------|----------------------------|--------------------------|
| Blue BG        | `rgba(46,155,204,.08)`     | Subtle blue icon/badge backgrounds |
| Pine BG        | `rgba(45,107,63,.07)`      | Subtle green icon/badge backgrounds |

---

## Typography

| Role    | Font             | Weight  | Usage                                        |
|---------|------------------|---------|----------------------------------------------|
| Display | Playfair Display | 800     | Hero headline, section titles, pricing numbers, card titles |
| Heading | DM Sans          | 500–700 | Nav, buttons, labels, feature titles, subheads, UI text |
| Body    | Lora             | 400–500 | Paragraph descriptions, long-form text       |

### Google Fonts Import
```
https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Lora:wght@400;500;600&display=swap
```

---

## Logo

### Mark
Solid blue fish silhouette (`#2E9BCC`) with eye detail and tail fin.

### Wordmark
`FISHON` in DM Sans 700, uppercase, letter-spacing 2px.

### SVG Fish Icon
```svg
<path d="M34 25C34 25 27 14 18 14C10 14 5 18.5 5 25C5 31.5 10 36 18 36C27 36 34 25 34 25Z" fill="#2E9BCC"/>
<circle cx="12.5" cy="23.5" r="2" fill="[bg-outer-ring]"/>
<circle cx="12.5" cy="23.5" r="1.3" fill="[bg-iris]"/>
<circle cx="13" cy="23" r=".5" fill="[bg-pupil]"/>
<path d="M34 25L42 18L39.5 25L42 32L34 25Z" fill="#2E9BCC"/>
```

### Variations

| Variant    | Fish   | Eye           | Text      | Background |
|------------|--------|---------------|-----------|------------|
| On Dark    | Blue   | White iris    | White     | `#3D3528`  |
| On Tan     | Blue   | Dark iris     | `#3D3528` | `#EDE8E0`  |
| On White   | Blue   | White iris    | `#3D3528` | `#FFFFFF`  |
| On Blue    | White  | Blue iris     | —         | `#2E9BCC`  |

---

## Layout Pattern

| Section          | Background  | Text Color     |
|------------------|-------------|----------------|
| Nav              | Dark Brown  | White          |
| Hero             | Photo + dark overlay | White  |
| Stats Bar        | Warm Tan    | Blue numbers   |
| Features         | Warm Tan    | Dark Brown     |
| Photo Break      | Full-bleed image | —         |
| Map Preview      | Dark Brown  | White          |
| How It Works     | Warm Tan    | Dark Brown     |
| Photo Break      | Full-bleed image | —         |
| Pricing          | Warm Tan    | Dark Brown     |
| Footer           | Dark Brown  | Muted white    |

---

## Brand Voice

| Context            | Tone                     | Example                                                                 |
|--------------------|--------------------------|-------------------------------------------------------------------------|
| Push Notification  | Excited, data-first      | "Fish on! Strawberry just got 10,000 rainbows. Water temp: 52°F. Go get 'em." |
| App Store          | Confident, direct        | "Every stocking report, river flow, and fishing condition in America — live on a map." |
| Social Post        | Short, punchy            | "10,000 rainbows just dropped in Strawberry. 52°F. Flows: perfect. This is your weekend." |
| Email Subject      | Personal, specific       | "Your water report: 3 stockings near you this week" |
| Error State        | Honest, still useful     | "Conditions data is temporarily unavailable. Last known: 342 CFS at 2:15 PM." |
| Brand Motto        | Five words               | "All your water. One app." |

### Voice Rules
- Lead with data, end with action
- No fluff, no filler
- Numbers over adjectives ("10,000 rainbows" not "a big stocking")
- Speak like an angler texting a buddy, not a brand posting content
