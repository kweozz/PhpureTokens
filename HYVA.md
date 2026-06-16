# Hyvä compatibility

**Short answer: yes.** This component overview is built specifically so a Hyvä developer can lift any component into a `.phtml` template without rewriting the styling. Every visual value comes from `--*` CSS custom properties that Tailwind v4 expects via `@theme`, and every HTML structure is plain (no JS framework, no client-side hydration).

## Tech-stack mapping

| Layer | This repo | Hyvä project |
|---|---|---|
| Design tokens (source) | `tokens/` — Tokens Studio JSON (core / brand / semantic / component / viewport) | Same file, synced via Tokens Studio plugin in Figma |
| Token compile | `python3 build-tokens.py` → `tokens.css` | Style Dictionary + `sd-transforms` (already in the spec) → same `tokens.css` |
| Token consumption | `<link rel="stylesheet" href="tokens.css">` in the docs site | `@theme { … }` block in `tailwind.config.css` — vars become utility classes (`bg-background-default`, `text-text-brand`, etc.) |
| Component markup | Plain HTML in `index.html` (with `class="product-card"` etc.) | Drop the same markup into a Hyvä `.phtml` partial; replace static text with `$_block->getMethod()` and the `escapeHtml()` helpers |
| Component styles | `components.css` (this repo) | Same file, imported by Hyvä's main CSS bundle, or refactored into per-component CSS partials |
| Brand switching | `<body data-brand="golf">` toggled via JS in the docs site | Same attribute applied server-side in the Magento layout XML or in a `1column.phtml` wrapper — no JS needed |
| Responsive | Media queries in `tokens.css` swap `--font-size-*` vars at the `md` and `sm` breakpoints | Same, no change needed |

## Mapping a component to a Hyvä template

Take the product card. The repo version is:

```html
<article class="product-card">
  <span class="product-card__tag">New</span>
  <div class="product-card__media-wrap">
    <img class="product-card__media" src="…" alt="" />
  </div>
  <span class="product-card__brand">Druids</span>
  <h3 class="product-card__title">Flyknit Racer</h3>
  <span class="product-card__price">€99.99</span>
  <div class="product-card__actions">
    <button class="btn btn--primary product-card__cart">…Add to cart</button>
    <button class="product-card__wishlist" aria-label="…">…</button>
  </div>
</article>
```

The Hyvä `.phtml` version is the same markup with Magento data wired in:

```php
<?php
/** @var \Magento\Catalog\Block\Product\ListProduct $block */
/** @var \Magento\Catalog\Model\Product $_product */
$_product = $block->getProduct();
$helper = $this->helper(\Magento\Catalog\Helper\Output::class);
?>
<article class="product-card" data-sku="<?= $block->escapeHtml($_product->getSku()) ?>">
  <?php if ($_product->getNewsFromDate()): ?>
    <span class="product-card__tag"><?= $block->escapeHtml(__('New')) ?></span>
  <?php endif; ?>
  <div class="product-card__media-wrap">
    <img class="product-card__media"
         src="<?= $block->escapeUrl($block->getImage($_product, 'category_page_grid')->getImageUrl()) ?>"
         alt="<?= $block->escapeHtmlAttr($_product->getName()) ?>" />
  </div>
  <span class="product-card__brand"><?= $block->escapeHtml($_product->getAttributeText('brand') ?: '') ?></span>
  <h3 class="product-card__title">
    <a href="<?= $block->escapeUrl($_product->getProductUrl()) ?>">
      <?= $block->escapeHtml($_product->getName()) ?>
    </a>
  </h3>
  <span class="product-card__price"><?= $block->getProductPriceHtml($_product, 'final_price') ?></span>
  <div class="product-card__actions">
    <button class="btn btn--primary product-card__cart" data-mage-init='{"addToCart": {…}}'>
      <svg>…</svg> <?= $block->escapeHtml(__('Add to cart')) ?>
    </button>
    <button class="product-card__wishlist" aria-label="<?= $block->escapeHtmlAttr(__('Add to wishlist')) ?>">
      <svg>…</svg>
    </button>
  </div>
</article>
```

The classes are unchanged. Tailwind v4 picks them up via the `@theme` block, so the cream surface, padding, button radius and brand color all come from the same tokens.

## Tailwind v4 `@theme` setup (per the original CLAUDE.md)

```css
/* main.css */
@import "tailwindcss";

@theme {
  /* surface */
  --color-background-default: theme(--color-background-default);
  /* …or simply import tokens.css before this block: the @theme cascade reads :root */
}
@import "./tokens.css";       /* sets :root / [data-brand="mini-golf"] / @media */
@import "./components.css";   /* component class definitions */
```

Anything Tailwind sees in `@theme` becomes a utility:

```html
<div class="bg-background-default text-text-brand p-md rounded-lg">…</div>
```

`bg-background-default` resolves to `var(--color-background-default)`. Brand swap on a parent flips it.

## Brand switching — Magento layout

In a Hyvä project, set the brand once at the root layout. Two practical options:

**A) Per-store config (recommended).** Add a custom config flag (e.g. `phpure/brand/active`) read in `1column.phtml`:

```php
<?php
$brand = $this->_scopeConfig->getValue('phpure/brand/active', \Magento\Store\Model\ScopeInterface::SCOPE_STORE) ?: 'golf';
?>
<body data-brand="<?= $block->escapeHtmlAttr($brand) ?>">
```

**B) Per category / per route.** Read the current category and set `data-brand` accordingly (mini-golf for `/kids`, etc.).

Either way: all components stay brand-agnostic — they reference `--button-primary-*`, not `--brand-color-primary-500`.

## What still has to be done in your Hyvä project

This repo gives you the **design source of truth**. To roll it into Hyvä you'll need to:

1. Run `npm` setup for `style-dictionary` + `@tokens-studio/sd-transforms` in your `app/design/frontend/<vendor>/<theme>/` (mirrors what `build-tokens.py` does here in Python; the JSON source is identical).
2. Drop the generated `tokens.css` into your Hyvä theme's CSS entry, import before Tailwind processes.
3. Copy `components.css` (or split it per-component) into the same CSS entry.
4. Convert each `.html` block in `index.html` into a Hyvä `.phtml` partial, replacing static content with Magento block calls and adding any `data-mage-init` JS hooks (cart, wishlist, search).
5. Wire `data-brand` on the layout `<body>` per the section above.

This repo is the spec; your Hyvä theme is the implementation.

## What's deliberately NOT in this repo

- Magento blocks, layouts, or PHP — by design, this is the *visual* source of truth, decoupled from any backend
- A JS framework — components are static HTML; interactive bits (cart, wishlist, header sticky) get wired with Hyvä's Alpine + minimal JS in the `.phtml` layer
- A build chain — `tokens.css` is committed so you can preview locally without `npm` / Style Dictionary. Your Hyvä project should regenerate it from `tokens/` on every theme build
