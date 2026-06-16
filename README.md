# PHPure · Components

A shadcn-style overview of the PHPure design-system components, bound to the multi-brand token set (**golf** + **mini-golf**) for Hyvä / Magento (Tailwind v4).

## What's in here

```
phpure-components/
├── index.html           — the docs site
├── tokens.css           — generated CSS custom properties (golf + mini-golf + viewport)
├── components.css       — component styles bound only to tokens
├── site.css             — docs chrome (sidebar / topbar / preview frame)
├── build-tokens.py      — resolves tokens/ → tokens.css
└── tokens/              — Tokens-Studio source (core / brand / semantic / component / viewport)
```

## Brand-switching

Every component is brand-agnostic — they reference `--button-*`, `--color-*`, etc. The top bar's toggle sets `data-brand="mini-golf"` on `<body>`, and the same component re-skins live.

```css
:root                    { /* golf = default */ }
[data-brand="mini-golf"] { /* mini-golf overrides */ }
```

## Responsive

Viewport toggle in the top bar constrains the preview width. Real font-size shifts happen automatically via media queries (`max-width: 960px`) generated from `tokens/viewport/small.json`.

## Rebuilding tokens

```bash
python3 build-tokens.py
```

Source of truth is `tokens/`. Never edit `tokens.css` by hand.

## What's inside

- **Foundations**: colors, typography, spacing, radius, shadow
- **Components**: button, link, form, tag, card, product card, category card
- **Blocks**: header, hero, CTA banner, image CTA, testimonial, review, USPs, story card, video highlight, footer

## License

Internal — PHPure.
