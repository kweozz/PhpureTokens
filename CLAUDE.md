# CLAUDE.md — PHPure · Vibecoding Hyvä componenten met design tokens

## Doel
Je bouwt frontend-componenten voor PHPure (multi-brand e-commerce op Hyvä/Magento, Tailwind v4). Twee bronnen werken samen:

- **Figma (via MCP)** → de **layout en structuur**: wat een component moet zijn, hoe het eruitziet, welke elementen erin zitten, spacing-verhoudingen, hiërarchie. Gebruik dit om te zien WAT je bouwt.
- **`tokens.json`** (dit design-tokensysteem) → het **hoe**: welke exacte kleuren, fonts, radii, shadows. Gebruik dit voor ALLE visuele waarden.

**Belangrijk:** de Figma-file is NIET verbonden met de tokens. Gebruik Figma dus alleen voor layout/structuur en pixel-verhoudingen — neem nooit hardcoded kleurwaarden of font-namen uit Figma over. Elke visuele waarde komt uit `tokens.json`. Als Figma een groene knop toont, gebruik je `--button-primary-bg-default`, niet de hex die Figma rapporteert.

---

## Token-architectuur (4 lagen)

```
core        → primitieven (kleurschalen, spacing, fontSize, breakpoint, shadow, radius)
brand/<x>   → merk-eigen primitieven (primary/secondary/tertiary kleuren + fonts)
semantic/<x>→ betekenislaag (color.background/text/border, typography, spacing)
component/<x>→ component-tokens (button, link, form, card)
```

**Regel:** componenten binden aan `component/*` of `semantic/*`. NOOIT rechtstreeks aan `core` of `brand`.

Merken: **golf** (default) en **mini-golf**. Per merk een eigen `brand/`, `semantic/` en `component/` set. De waarden verschillen, de structuur is identiek.

---

## Hoe tokens CSS custom properties worden

Bij export (Style Dictionary + sd-transforms) wordt elk token een CSS-variabele. Patroon: `{laag}.{pad}` → `--pad-met-streepjes`. Voorbeelden:

```
semantic.color.background.default  → var(--color-background-default)
semantic.color.text.default        → var(--color-text-default)
component.button.primary.color.background.default → var(--button-primary-background-default)
```

Gebruik altijd `var(--...)`. Nooit een hex, font-naam of px die in de tokens staat hardcoden.

---

## Semantische tokens (gebruik deze als er geen component-token is)

**Background:** `brand-strong, brand-subtle, brand-knockout, default, muted, muted-soft, subtle-hover, disabled, overlay, overlay-strong`
**Text:** `default, brand, subtle, knockout, disabled, placeholder, accent`
**Border:** `default, default-hover, strong, subtle, knockout, disabled, focus, focus-knockout`

**Typography (composite — appliceer als 1 stijl):**
`display, headline-lg, headline, headline-sm, title-lg, title, title-sm, body-lg, body, body-sm, label-lg, label, label-sm, logo`

Elke typografie-stijl bevat al fontFamily + fontWeight + fontSize + lineHeight + letterSpacing. Gebruik de hele stijl, stel die properties niet los in.

---

## Component-tokens (Tier 3 — gebruik deze eerst)

### Button — varianten: primary, secondary, tertiary
Elke variant heeft per `color.background / color.content / color.border` de states:
`default, hover, active, disabled` (+ border ook `focus`).
Primary heeft daarnaast `borderRadius.default`.

```
--button-primary-background-default / -hover / -active / -disabled
--button-primary-content-default / -hover / -active / -disabled
--button-primary-border-default / -hover / -active / -focus / -disabled
--button-primary-borderRadius-default
```
(idem voor secondary en tertiary)

### Link — standaard + knockout (op donkere achtergrond)
```
--link-content-default / -hover / -active / -visited
--link-knockout-content-default / -hover / -active / -visited
```

### Form
```
--form-background-default / -focus / -hover / -active / -disabled
--form-border-default / -hover / -active / -focus / -disabled
--form-content-default / -disabled
```

### Card
```
--card-background-default / -focus / -hover / -active / -disabled
--card-border-default / -hover / -active / -focus / -disabled
--card-content-default / -disabled
--card-image-height
--card-padding-horizontal / -vertical
--card-tags-padding
--card-tags-borderRadius-top / -bottom
```

---

## Brand-switching

Per merk een andere set waarden onder dezelfde variabelenamen. In CSS via een attribuut op een parent:

```css
:root                    { /* golf = default */ }
[data-brand="mini-golf"] { /* mini-golf overrides */ }
```

Componenten zijn brand-agnostisch: ze verwijzen alleen naar `--button-*`, `--color-*` etc. — die wisselen vanzelf mee.

---

## Responsive / breakpoints

Breakpoints staan in `core.breakpoint`:
```
sm = 560px   md = 960px   lg = 2000px (container max)
```

Font-sizes wisselen per viewport (token sets `viewport/large` en `viewport/small`). In CSS vertaalt dat naar media queries die de font-size-variabelen overschrijven:

```css
:root { --font-size-display: 72px; }      /* large/desktop */
@media (max-width: 960px) { /* md */ }
@media (max-width: 560px)  { --font-size-display: 40px; }  /* small/mobile */
```

---

## Hyvä-context

- Templates zijn `.phtml`-bestanden met Tailwind v4 utility-classes.
- Tailwind v4 gebruikt CSS-first config via `@theme` — de tokens landen daar als `--color-*`, `--font-size-*`, `--spacing-*` en worden automatisch utility-classes (`bg-background-default`, `text-text-default`).
- Gebruik utility-classes waar mogelijk; `@apply` alleen voor herhalende patronen; losse CSS alleen als een token-var niet als utility bestaat.

---

## Werkwijze per component

1. **Bekijk de layout in Figma (MCP)** — structuur, elementen, verhoudingen, states.
2. **Check `component/*`** of er al tokens voor bestaan (button, link, form, card hebben ze).
3. **Zo niet:** gebruik `semantic/*` tokens.
4. **Schrijf de markup + classes** met `var(--...)` / token-utilities. Nooit hardcoded waarden uit Figma.
5. **Implementeer alle states**: default / hover / active / disabled / focus. Focus altijd met `--color-border-focus`.
6. **Test brand-switch**: zet `data-brand="mini-golf"` op de parent — het component moet visueel veranderen maar niet breken.

---

## Verboden

- Geen hardcoded hex, rgb of font-namen (ook niet als Figma ze toont)
- Geen losse typografie-properties — gebruik de composite stijl
- Geen binding aan `core` of `brand` rechtstreeks vanuit een component
- Geen nieuwe tokens verzinnen — gebruik wat in `tokens.json` staat
- Geen `!important` om tokenwaarden te overschrijven

---

## Bestanden in deze repo

- `tokens.json` — het volledige design-tokensysteem (bron van waarheid voor alle visuele waarden)
- Figma via MCP — bron voor layout/structuur (NIET voor kleurwaarden)
- Hyvä UI library / theme — de componentstructuur en conventies waarbinnen je werkt
