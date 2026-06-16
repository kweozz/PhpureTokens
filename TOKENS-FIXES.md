# Token sync — what to fix in Tokens Studio

When comparing your current Tokens Studio export to the **original Figma variables** (`design-tokens-original.zip`, which is the version still connected to the designs), I found 7 gaps. **2 are already auto-patched in this repo's `tokens/`** (so the demo site renders correctly), but **5 belong in Tokens Studio itself** so the brand-differentiation design logic survives future exports.

## ✅ Already patched in this repo (small fixes)

| File | Fix |
|---|---|
| `tokens/semantic/golf.json` | `background.muted-soft` no longer references `brand.color.offWhite.50` (golf has no offWhite scale) — points at `core.color.neutral.50` instead |
| `tokens/semantic/golf.json` | `fontWeight.title` is now `medium` (was `regular`) — original Tier 2 specs title as medium |
| `tokens/semantic/mini-golf.json` | The `radius` key was renamed to `borderRadius` so components referencing `semantic.borderRadius.*` resolve correctly |
| `tokens/semantic/{golf,mini-golf}.json` | Added `typography.meta` and `typography.meta-sm` composites (14px / 12px medium) |
| `tokens/viewport/{large,small}.json` | Added `fontSize.meta` and `fontSize.meta-sm` |

You should reproduce these in Tokens Studio so future exports don't regress.

## ⚠️ TODO in Tokens Studio — the brand-differentiation gaps

These are the ones that actually make Golf and Mini-Golf *feel* like different brands. Right now both look the same shape with the same type rhythm.

### 1. Mini-Golf typography needs **bolder** headings

The original Tier 2 Mini-Golf has display/headline at `font-weight.bold`, while Golf has them at `medium`. Today both your brands use `medium`.

In Tokens Studio, under `semantic/mini-golf`:

```json
"fontWeight": {
  "display":  { "$value": "{core.fontWeight.bold}" },
  "heading":  { "$value": "{core.fontWeight.bold}" },
  "title":    { "$value": "{core.fontWeight.medium}" },
  "body":     { "$value": "{core.fontWeight.regular}" },
  "label":    { "$value": "{core.fontWeight.medium}" }
}
```

Keep `semantic/golf` as `medium / medium / medium / regular / bold` (the design-intent).

### 2. Mini-Golf needs a **secondary font** for titles

The original assigns a `Secondary_font` (playful, kid-feeling) to `title-lg / title-default / title-sm` on mini-golf only. Today your mini-golf inherits the same `ITC Avant Garde Gothic Pro` body font as golf — so mini-golf titles feel adult.

In `core/fontFamily` add:

```json
"grenadine-mvb": { "$type": "fontFamilies", "$value": "Grenadine MVB" }
```

Then in `semantic/mini-golf.fontFamily` add a third role:

```json
"fontFamily": {
  "heading": { "$value": "{core.fontFamily.dejanire-headline}" },
  "body":    { "$value": "{core.fontFamily.itc-avant-garde}" },
  "title":   { "$value": "{core.fontFamily.grenadine-mvb}" },
  "logo":    { "$value": "{core.fontFamily.dejanire-headline}" }
}
```

And update `typography.title-lg / title / title-sm` in mini-golf to reference `{semantic.fontFamily.title}` instead of `{semantic.fontFamily.body}`.

### 3. Border-radius scales should differ per brand

The original makes Mini-Golf visibly **rounder** (kid-friendly) and Golf **sharper**:

| token | Golf (sleek) | Mini-Golf (rounded) |
|---|---|---|
| `borderRadius.xs` | 0 | 8 |
| `borderRadius.sm` | 8 | 12 |
| `borderRadius.md` | 0 | 16 |
| `borderRadius.lg` | 12 | 32 |
| `borderRadius.xl` | 16 | round (pill) |
| `borderRadius.2xl` | 24 | round |
| `borderRadius.pill` / `max` | round | round |

Today your two brands collapsed to roughly the same scale. Re-derive both per the original.

### 4. Button primary radius differs per brand

The original makes:
- Golf `button.primary.borderRadius.default = border.radius.max` (full pill)
- Mini-Golf `button.primary.borderRadius.default = border.radius.8` (slightly rounded **rectangle**, not pill)

Today your mini-golf button.primary resolves to `semantic.borderRadius.sm` (12px). That's closer but not aligned. Update `component/mini-golf.json`:

```json
"borderRadius": {
  "default": { "$value": "{core.borderRadius.8}" }
}
```

### 5. Mobile typography variants

Each typography style in the original has a `-mobile` companion where font-size **and** font-weight can shift. E.g. mini-golf headline is `bold` on desktop but `medium` on mobile to keep the rhythm.

Two approaches:

- **Option A (simple, what I do today)**: only swap `font-size` via `viewport/small`. Loses the weight shift.
- **Option B (faithful to original)**: declare per-style mobile variants under `semantic/{brand}.typography` (e.g. `headline-mobile`), and pick the right one in CSS via media query.

If you want fidelity, do option B. I'd duplicate each `display / headline-lg / headline / headline-sm / title-lg / title-sm` with `-mobile` siblings that point at the small viewport font-size and the mobile-specific weight.

## Sanity checklist after re-exporting Tokens Studio

After applying the above, re-export and run:

```bash
python3 build-tokens.py
grep -c "unresolved" tokens.css   # should print 0
```

If anything still falls back to `inherit`, the compiler will leave a `/* unresolved ref: {…} */` comment pointing at the offending path.
