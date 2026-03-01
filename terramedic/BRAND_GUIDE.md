# Terramedic Brand Guide

> **Design System**: Earth Guardian (dark, bold, space-themed)
> **WCAG Target**: AA compliance for all text/background pairings

---

## Brand Overview

Terramedic is an environmental action platform connecting people with
volunteer opportunities, donation options, and daily sustainability
practices. The "Earth Guardian" design system evokes the overview effect --
seeing Earth from space -- to inspire urgency and stewardship.

**Design philosophy**: Dark backgrounds convey the vastness of space;
bright accent colors (green, blue, gold) represent hope and action.
Every color pairing must meet WCAG AA contrast requirements.

---

## Logo

### The Green Cross

A bold green cross -- like the Red Cross, but green. Signals environmental first aid.

Two SVG variants exist:

#### Cross-only mark (`static/images/logo.svg`)

```text
ViewBox: 7 7 26 26
```

| Element        | Attributes                                          |
| -------------- | --------------------------------------------------- |
| Vertical arm   | `x=15 y=7 width=10 height=26 rx=1.5 fill="#2ecc71"` |
| Horizontal arm | `x=7 y=15 width=26 height=10 rx=1.5 fill="#2ecc71"` |

#### Favicon variant (`static/favicon.svg`)

Cross on a white circle background, for use at small sizes in browser tabs.

```text
ViewBox: 0 0 40 40
```

| Element           | Attributes                                          |
| ----------------- | --------------------------------------------------- |
| Background circle | `cx=20 cy=20 r=20 fill="white"`                     |
| Vertical arm      | `x=15 y=7 width=10 height=26 rx=1.5 fill="#2ecc71"` |
| Horizontal arm    | `x=7 y=15 width=26 height=10 rx=1.5 fill="#2ecc71"` |

### Sizing

| Context   | Size    | Usage                       |
| --------- | ------- | --------------------------- |
| Favicon   | 16px    | Browser tab                 |
| Navbar    | 32-40px | Brand mark next to wordmark |
| Hero/Card | 48-64px | Feature placement           |

### Clear Space

Maintain a minimum clear space of 25% of the logo diameter on all sides
(e.g., 10px clear space around a 40px logo).

### Wordmark

All-lowercase **"terramedic"** in white.
Font: Montserrat Bold (700), tracking -0.02em.

### Do's and Don'ts

**Do**:

- Use the SVG at any size (it's resolution-independent)
- Use the B&W variant (swap green for black) on light backgrounds
- Pair with the wordmark at navbar scale

**Don't**:

- Stretch or distort the proportions
- Place on backgrounds that reduce contrast below 3:1
- Recolor the cross to anything other than green or black
- Add drop shadows, outlines, or effects to the logo

---

## Color Palette

### Primary Colors

| Token       | Hex       | CSS Variable    | Usage                      |
| ----------- | --------- | --------------- | -------------------------- |
| Space Black | `#0a0e17` | `--space-black` | Page background, dark text |
| Deep Navy   | `#0f1829` | `--deep-navy`   | Navbar, input backgrounds  |
| Navy        | `#162033` | `--navy`        | Cards, form containers     |

### Accent Colors

| Token            | Hex       | CSS Variable               | Usage                          |
| ---------------- | --------- | -------------------------- | ------------------------------ |
| Terra Green      | `#2ecc71` | `--terra-green-color`      | Hero CTA, logo, card accents   |
| Terra Green Dark | `#1a9c54` | `--terra-dark-green-color` | Available (not actively used)  |
| Terra Blue       | `#2196f3` | `--terra-blue-color`       | Links, card accents            |
| Terra Dark Blue  | `#0f1829` | `--terra-dark-blue-color`  | Available (same as Deep Navy)  |
| Sunrise Gold     | `#f39c12` | `--sunrise-gold`           | Highlights, external links     |
| Vibrant Plum     | `#7c3aed` | `--btn-purple`             | Other Actions accent & buttons |

#### Button Colors (ADA-Compliant for White Text)

Darker shades of each accent color, used exclusively for button
backgrounds so that white text passes WCAG AA (4.5:1+). The lighter
primary accent colors remain for text links, card accents, the logo,
and other decorative uses.

| Token               | Hex       | CSS Variable         | White Contrast | Usage                      |
| ------------------- | --------- | -------------------- | -------------- | -------------------------- |
| Button Blue         | `#1565c0` | `--btn-blue`         | 5.7:1 (AA)     | Volunteer buttons          |
| Button Blue Hover   | `#0d47a1` | `--btn-blue-hover`   | 8.7:1 (AAA)    | Volunteer button hover     |
| Button Green        | `#15803d` | `--btn-green`        | 5.1:1 (AA)     | Donate buttons             |
| Button Green Hover  | `#116630` | `--btn-green-hover`  | 7.2:1 (AAA)    | Donate button hover        |
| Button Gold         | `#a16207` | `--btn-gold`         | 4.9:1 (AA)     | Reserved (not active)      |
| Button Gold Hover   | `#7d4e06` | `--btn-gold-hover`   | 7.5:1 (AAA)    | Reserved (not active)      |
| Button Purple       | `#7c3aed` | `--btn-purple`       | 5.7:1 (AA)     | Other Actions buttons      |
| Button Purple Hover | `#6d28d9` | `--btn-purple-hover` | 7.1:1 (AAA)    | Other Actions button hover |

### Text Colors

| Token            | Hex       | Tailwind Class   | Usage                        |
| ---------------- | --------- | ---------------- | ---------------------------- |
| Text Primary     | `#ffffff` | `text-white`     | Headings, body on dark bg    |
| Text Secondary   | `#b0bec5` | `text-[#b0bec5]` | Subtitles, muted text        |
| Gray 400         | `#9ca3af` | `text-gray-400`  | Labels, links, section heads |
| Red 400          | `#f87171` | `text-red-400`   | Error messages               |
| Green 400        | `#4ade80` | `text-green-400` | Success messages             |
| White on Buttons | `#ffffff` | `text-white`     | Button text on btn-\* bg     |

---

## Typography

### Font Stack

| Role     | Font         | Weight  | CSS                           |
| -------- | ------------ | ------- | ----------------------------- |
| Headings | Montserrat   | 700-800 | `font-[Montserrat] font-bold` |
| Body     | Inter        | 300-600 | `font-sans` (default)         |
| Serif    | Merriweather | 300-900 | `font-serif`                  |

### Type Scale

| Element | Size (mobile)  | Size (desktop) | Weight | Tracking        |
| ------- | -------------- | -------------- | ------ | --------------- |
| H1      | 1.875rem (3xl) | 3.75rem (6xl)  | Bold   | tracking-tight  |
| H2      | 1.5rem (2xl)   | 2.25rem (4xl)  | Bold   | tracking-tight  |
| H3      | 1.25rem (xl)   | 1.5rem (2xl)   | Bold   | tracking-tight  |
| Body    | 1rem (base)    | 1.125rem (lg)  | Normal | normal          |
| Caption | 0.75rem (xs)   | 0.875rem (sm)  | Normal | normal          |
| Tagline | 0.875rem (sm)  | 1rem (base)    | 600    | tracking-widest |

---

## WCAG AA Contrast Table

Minimum ratios: **4.5:1** for normal text, **3:1** for large text (18pt+ or 14pt bold).

### Text on Dark Backgrounds

| Foreground            | Background            | Ratio  | Normal | Large |
| --------------------- | --------------------- | ------ | ------ | ----- |
| White `#ffffff`       | Space Black `#0a0e17` | 19.1:1 | PASS   | PASS  |
| White `#ffffff`       | Deep Navy `#0f1829`   | 17.4:1 | PASS   | PASS  |
| White `#ffffff`       | Navy `#162033`        | 14.4:1 | PASS   | PASS  |
| Gray 400 `#9ca3af`    | Space Black `#0a0e17` | 7.5:1  | PASS   | PASS  |
| Gray 400 `#9ca3af`    | Deep Navy `#0f1829`   | 6.8:1  | PASS   | PASS  |
| Gray 400 `#9ca3af`    | Navy `#162033`        | 5.7:1  | PASS   | PASS  |
| Red 400 `#f87171`     | Space Black `#0a0e17` | 6.6:1  | PASS   | PASS  |
| Red 400 `#f87171`     | Deep Navy `#0f1829`   | 6.0:1  | PASS   | PASS  |
| Red 400 `#f87171`     | Navy `#162033`        | 5.0:1  | PASS   | PASS  |
| Green 400 `#4ade80`   | Space Black `#0a0e17` | 9.3:1  | PASS   | PASS  |
| Terra Green `#2ecc71` | Space Black `#0a0e17` | 7.7:1  | PASS   | PASS  |

### White Text on Button Colors

| Foreground      | Background                    | Ratio | Normal | Large |
| --------------- | ----------------------------- | ----- | ------ | ----- |
| White `#ffffff` | Button Blue `#1565c0`         | 5.7:1 | PASS   | PASS  |
| White `#ffffff` | Button Blue Hover `#0d47a1`   | 8.7:1 | PASS   | PASS  |
| White `#ffffff` | Button Green `#15803d`        | 5.1:1 | PASS   | PASS  |
| White `#ffffff` | Button Green Hover `#116630`  | 7.2:1 | PASS   | PASS  |
| White `#ffffff` | Button Gold `#a16207`         | 4.9:1 | PASS   | PASS  |
| White `#ffffff` | Button Gold Hover `#7d4e06`   | 7.5:1 | PASS   | PASS  |
| White `#ffffff` | Button Purple `#7c3aed`       | 5.7:1 | PASS   | PASS  |
| White `#ffffff` | Button Purple Hover `#6d28d9` | 7.1:1 | PASS   | PASS  |

### Prohibited Pairings (FAIL)

| Foreground         | Background             | Ratio | Status   |
| ------------------ | ---------------------- | ----- | -------- |
| White `#ffffff`    | Terra Green `#2ecc71`  | 2.5:1 | FAIL     |
| White `#ffffff`    | Terra Blue `#2196f3`   | 3.7:1 | FAIL\*   |
| White `#ffffff`    | Sunrise Gold `#f39c12` | 2.6:1 | FAIL     |
| Gray 500 `#6b7280` | Space Black `#0a0e17`  | 4.1:1 | FAIL     |
| Gray 500 `#6b7280` | Deep Navy `#0f1829`    | 3.7:1 | FAIL     |
| Red 500 `#ef4444`  | Space Black `#0a0e17`  | 4.7:1 | marginal |
| Red 500 `#ef4444`  | Deep Navy `#0f1829`    | 4.3:1 | FAIL     |

\*White on Terra Blue passes for large bold text only (3.7:1 > 3:1).

---

## Approved Pairings Quick Reference

### Do

- **Buttons** (green, blue, gold): Use `text-white` on darker
  button-shade backgrounds (`--btn-green`, `--btn-blue`, `--btn-gold`)
- **Labels & section headings**: Use `text-gray-400` on any dark background
- **Error messages**: Use `text-red-400` on any dark background
- **Success messages**: Use `text-green-400` on any dark background
- **Body text**: Use `text-white` or `text-gray-400` on dark backgrounds
- **Links in footer**: Use `text-gray-400` with `hover:text-white`

### Don't

- Never use `text-white` on the lighter accent colors
  (`#2ecc71`, `#2196f3`, `#f39c12`) — only on darker button shades
- Never use `text-gray-500` on dark backgrounds (Space Black, Deep Navy, Navy)
- Never use `text-red-500` on dark backgrounds -- use `text-red-400` instead
- Never place low-contrast text-secondary (`#b0bec5`) at sizes below 14px without checking ratio

---

## Component Color Reference

### Navbar

| Element             | Color                 | Class / Style                             |
| ------------------- | --------------------- | ----------------------------------------- |
| Background          | Deep Navy `#0f1829`   | `background-color: #0f1829`               |
| Nav links           | White `#ffffff`       | `color: white; font-weight: 600`          |
| Active link         | White + underline     | `text-decoration: underline`              |
| Hover state         | White on rgba overlay | `background-color: rgba(255,255,255,0.1)` |
| Warming stripes bar | Gradient              | See Warming Stripes section               |

### Hero

| Element         | Color                  | Class / Style             |
| --------------- | ---------------------- | ------------------------- |
| Background      | Radial ellipse → black | `.hero-space-bg` gradient |
| Video           | Earth from space       | `<video>` in `.earth`     |
| Dark scrim      | Black gradient overlay | `.hero-scrim` (z-index 5) |
| Tagline         | Terra Green `#2ecc71`  | `text-terra-green`        |
| Title           | White `#ffffff`        | `text-white`              |
| Description     | Gray 200               | `text-gray-200`           |
| CTA button bg   | Terra Green `#2ecc71`  | `bg-terra-green`          |
| CTA button text | Space Black `#0a0e17`  | `text-[#0a0e17]`          |
| CTA hover       | Green 400              | `hover:bg-green-400`      |

### Action Cards

| Element          | Color                    | Class / Style                |
| ---------------- | ------------------------ | ---------------------------- |
| Card background  | Navy `#162033`           | `.card`                      |
| Card border      | White 6% opacity         | `rgba(255,255,255,0.06)`     |
| Accent strip     | Blue / Green / Purple    | `.card-accent` (3px top bar) |
| Icon bg (blue)   | `rgba(33,150,243,0.15)`  | `.blue-icon`                 |
| Icon bg (green)  | `rgba(46,204,113,0.15)`  | `.green-icon`                |
| Icon bg (purple) | `rgba(124,58,237,0.15)`  | `.purple-icon`               |
| Card title       | White `#ffffff`          | `.card-title`                |
| Card body        | Text Secondary `#b0bec5` | `.card-description`          |
| Action link      | Matching accent color    | `.blue-action` etc.          |

### Forms (Contact, Signup)

| Element                 | Color                 | Class / Style                   |
| ----------------------- | --------------------- | ------------------------------- |
| Form background         | Navy `#162033`        | `bg-navy`                       |
| Input background        | Deep Navy `#0f1829`   | `bg-deep-navy`                  |
| Labels                  | Gray 400 `#9ca3af`    | `text-gray-400`                 |
| Input text              | White `#ffffff`       | `text-white`                    |
| Error text              | Red 400 `#f87171`     | `text-red-400`                  |
| Success bg              | Green 900/30          | `bg-green-900/30`               |
| Success text            | Green 400 `#4ade80`   | `text-green-400`                |
| Submit button (contact) | Button Blue `#1565c0` | `bg-btn-blue text-white`        |
| Submit button (signup)  | Terra Green `#2ecc71` | `bg-terra-green text-[#0a0e17]` |

### Footer

| Element             | Color                  | Class / Style                               |
| ------------------- | ---------------------- | ------------------------------------------- |
| Background          | `#060a12`              | `bg-[#060a12]`                              |
| Warming stripes bar | Simplified gradient    | `from-blue-500 via-yellow-400 to-red-600`   |
| Stripes height      | 6px                    | `h-1.5`                                     |
| Section headings    | Gray 400 `#9ca3af`     | `text-gray-400 uppercase`                   |
| Body text           | Gray 400               | `text-gray-400`                             |
| Links               | Gray 400 → White hover | `text-gray-400 hover:text-white`            |
| Brand name          | White `#ffffff`        | `text-white font-bold` (via Logo component) |
| Copyright           | Gray 400               | `text-gray-400`                             |

### Tags / Badges (OrganizationCard)

| Element    | Color                  | Class / Style                      |
| ---------- | ---------------------- | ---------------------------------- |
| Blue tag   | Blue 900/30 + Blue 400 | `bg-blue-900/30 text-blue-400`     |
| Green tag  | Green 900/30 + Green   | `bg-green-900/30 text-green-400`   |
| Purple tag | Purple 900/30 + Purple | `bg-purple-900/30 text-purple-400` |
| Shape      | Rounded full pill      | `rounded-full px-2.5 py-0.5`       |

---

## Special Elements

### Warming Stripes Gradient

Used as a thin accent strip below the navbar and above the footer. Represents the progression from
cooler (blue) to warmer (red) years in global temperature data.

```css
background: linear-gradient(
  90deg,
  #08306b 0%,
  #2171b5 15%,
  #6baed6 25%,
  #fed976 40%,
  #fd8d3c 55%,
  #e31a1c 70%,
  #bd0026 85%,
  #800026 100%
);
```

**Height**: 5px (`h-[5px]`)

CSS variable (extended version): `--warming-stripes-gradient`

### Hero Video Background

A looping, muted video of Earth from space fills the hero section.
A dark scrim gradient overlays the video for text legibility.

- **Video sources**: `static/videos/earth-hero.webm`, `.mp4`
- **Poster image**: `static/images/earth-hero-poster.jpg`
- **Scrim**: Linear gradient from 80% black (top) to transparent (bottom)

---

## Implementation Notes

### CSS Custom Properties

All color tokens are defined in `src/app.css` under `:root`:

```css
:root {
  --terra-blue-color: #2196f3;
  --terra-green-color: #2ecc71;
  --terra-dark-blue-color: #0f1829;
  --terra-dark-green-color: #1a9c54;
  --space-black: #0a0e17;
  --deep-navy: #0f1829;
  --navy: #162033;
  --sunrise-gold: #f39c12;
  --btn-blue: #1565c0;
  --btn-blue-hover: #0d47a1;
  --btn-green: #15803d;
  --btn-green-hover: #116630;
  --btn-gold: #a16207;
  --btn-gold-hover: #7d4e06;
  --btn-purple: #7c3aed;
  --btn-purple-hover: #6d28d9;
  --warming-stripes-gradient: linear-gradient(90deg, ...);
}
```

### Tailwind v4 Tokens

Custom colors are registered via the `@theme` block in `src/app.css`
(Tailwind v4 does **not** read `tailwind.config.js` for colors):

```css
@theme {
  --color-space-black: #0a0e17;
  --color-deep-navy: #0f1829;
  --color-navy: #162033;
  --color-terra-green: #2ecc71;
  --color-terra-dark-green: #1a9c54;
  --color-terra-blue: #2196f3;
  --color-terra-dark-blue: #0f1829;
  --color-sunrise-gold: #f39c12;
  --color-btn-blue: #1565c0;
  --color-btn-blue-hover: #0d47a1;
  --color-btn-green: #15803d;
  --color-btn-green-hover: #116630;
  --color-btn-gold: #a16207;
  --color-btn-gold-hover: #7d4e06;
  --color-btn-purple: #7c3aed;
  --color-btn-purple-hover: #6d28d9;
  --color-text-secondary: #b0bec5;
}
```

Use as Tailwind classes: `bg-terra-green`, `bg-navy`, `bg-btn-green`, etc.

Button text uses `text-white` on the darker `btn-*` backgrounds
for WCAG AA compliance. The lighter accent colors (`terra-green`,
`terra-blue`, `sunrise-gold`) are for links, card accents, and the
logo.

### Font Loading

Fonts are loaded via Google Fonts in `src/app.css`:

- **Inter** (300-800): Body text, UI elements (`font-sans`)
- **Montserrat** (100-900): Headings, brand text
- **Merriweather** (300-900): Serif accent (`font-serif`)
- **Pacifico**: Decorative script (available, rarely used)
