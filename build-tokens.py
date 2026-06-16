#!/usr/bin/env python3
"""
PHPure tokens → tokens.css

Resolves the Tokens-Studio multi-file source under ./tokens/ into a single
tokens.css with :root (golf default), [data-brand="mini-golf"] overrides,
viewport media queries, and typography utility classes.

Run:  python3 build-tokens.py
"""

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "tokens"
OUT = ROOT / "tokens.css"

FONT_WEIGHT_MAP = {
    "Light": "300",
    "Regular": "400",
    "Medium": "500",
    "Semibold": "600",
    "Bold": "700",
}

# Google-Fonts fallback chains for proprietary brand fonts so the brand identity
# is still visible even if the original .otf files are not licensed/loaded.
FONT_FALLBACK = {
    "Dejanire Headline": '"Dejanire Headline", "DM Serif Display", "Cormorant Garamond", serif',
    "ITC Avant Garde Gothic Pro": '"ITC Avant Garde Gothic Pro", "Jost", "Inter", system-ui, sans-serif',
    "Grenadine MVB": '"Grenadine MVB", "Fredoka", "Quicksand", system-ui, sans-serif',
    "DM Sans": '"DM Sans", system-ui, sans-serif',
    "Inter": '"Inter", system-ui, sans-serif',
}


def font_stack(name):
    return FONT_FALLBACK.get(name, f'"{name}", system-ui, sans-serif')


def load(p):
    with open(p) as f:
        return json.load(f)


def deep_merge(a, b):
    """Recursively merge b into a. b wins on leaves."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = deep_merge(a.get(k), v) if k in a else v
        return out
    return b


def resolve_refs(tree, root):
    """Walk tree, replacing {a.b.c} references in $value with the resolved literal."""
    REF_RE = re.compile(r"\{([^}]+)\}")

    def look_up(path):
        node = root
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if isinstance(node, dict) and "$value" in node:
            return resolve_value(node["$value"])
        return None

    def resolve_value(v):
        if isinstance(v, str):
            # full-string ref?
            m = re.fullmatch(r"\{([^}]+)\}", v)
            if m:
                got = look_up(m.group(1))
                return got if got is not None else v
            # inline refs (rare but support it)
            return REF_RE.sub(lambda mm: str(look_up(mm.group(1)) or mm.group(0)), v)
        if isinstance(v, dict):
            return {k: resolve_value(x) for k, x in v.items()}
        if isinstance(v, list):
            return [resolve_value(x) for x in v]
        return v

    def walk(node):
        if isinstance(node, dict):
            if "$value" in node and "$type" in node:
                node["$value"] = resolve_value(node["$value"])
            else:
                for k, v in node.items():
                    walk(v)

    walk(tree)
    return tree


def build_brand(brand):
    """Compose + resolve a full brand context."""
    ctx = {}
    ctx = deep_merge(ctx, load(SRC / "core.json"))
    ctx = deep_merge(ctx, load(SRC / "brand" / f"{brand}.json"))
    ctx = deep_merge(ctx, load(SRC / "semantic" / f"{brand}.json"))
    # source-token alias: mini-golf uses semantic.radius.*, components reference semantic.borderRadius.*
    sem = ctx.get("semantic", {})
    if "radius" in sem and "borderRadius" not in sem:
        sem["borderRadius"] = sem["radius"]
    ctx = deep_merge(ctx, load(SRC / "component" / f"{brand}.json"))
    ctx = deep_merge(ctx, load(SRC / "viewport" / "large.json"))
    return resolve_refs(ctx, ctx)


def build_viewport_overlay(brand, size):
    """Resolve viewport-only overrides for a media query."""
    ctx = {}
    ctx = deep_merge(ctx, load(SRC / "core.json"))
    ctx = deep_merge(ctx, load(SRC / "brand" / f"{brand}.json"))
    ctx = deep_merge(ctx, load(SRC / "viewport" / f"{size}.json"))
    return resolve_refs(ctx, ctx)["viewport"]["fontSize"]


# ---------- name mapping ----------
def kebab(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.lower()


def shadow_to_css(v):
    if isinstance(v, dict):
        return f"{v.get('x', 0)}px {v.get('y', 0)}px {v.get('blur', 0)}px {v.get('spread', 0)}px {v.get('color', '#0000')}"
    return v


def collect_vars(ctx):
    """Walk the resolved tree and yield (--var-name, css-value) tuples."""
    out = []

    sem_color = ctx.get("semantic", {}).get("color", {})
    for kind in ("background", "text", "border"):
        node = sem_color.get(kind, {})
        for path, value in flatten(node):
            out.append((f"--color-{kind}-{path}", value))

    for k, v in flat_leaves(ctx.get("semantic", {}).get("borderRadius", {})):
        out.append((f"--radius-{k}", v))
    for k, v in flat_leaves(ctx.get("semantic", {}).get("borderWidth", {})):
        out.append((f"--border-width-{k}", v))
    for k, v in flat_leaves(ctx.get("semantic", {}).get("spacing", {})):
        out.append((f"--spacing-{k}", v))
    for k, v in flat_leaves(ctx.get("semantic", {}).get("shadow", {})):
        out.append((f"--shadow-{k}", shadow_to_css(v)))
    for k, v in flat_leaves(ctx.get("semantic", {}).get("fontFamily", {})):
        out.append((f"--font-family-{k}", font_stack(v)))
    for k, v in flat_leaves(ctx.get("semantic", {}).get("fontWeight", {})):
        out.append((f"--font-weight-{k}", FONT_WEIGHT_MAP.get(v, v)))

    # typography composites — emit per-property vars
    typo = ctx.get("semantic", {}).get("typography", {})
    for name, node in typo.items():
        v = node.get("$value", {}) if isinstance(node, dict) else {}
        if not isinstance(v, dict):
            continue
        for prop in ("fontFamily", "fontWeight", "fontSize", "lineHeight", "letterSpacing"):
            if prop in v:
                val = v[prop]
                if prop == "fontFamily":
                    val = font_stack(val)
                elif prop == "fontWeight":
                    val = FONT_WEIGHT_MAP.get(val, val)
                out.append((f"--typography-{name}-{kebab(prop)}", val))

    for k, v in flat_leaves(ctx.get("viewport", {}).get("fontSize", {})):
        out.append((f"--font-size-{k}", v))

    # component.button.{variant}
    btn = ctx.get("component", {}).get("button", {})
    for variant, vnode in btn.items():
        color = vnode.get("color", {})
        for slot in ("background", "content", "border"):
            for state, val in flat_leaves(color.get(slot, {})):
                out.append((f"--button-{variant}-{slot}-{state}", val))
        for state, val in flat_leaves(vnode.get("borderRadius", {})):
            out.append((f"--button-{variant}-border-radius-{state}", val))

    # component.link
    link = ctx.get("component", {}).get("link", {})
    for state, val in flat_leaves(link.get("color", {}).get("content", {})):
        out.append((f"--link-content-{state}", val))
    for state, val in flat_leaves(link.get("knockout", {}).get("color", {}).get("content", {})):
        out.append((f"--link-knockout-content-{state}", val))

    # component.form
    form = ctx.get("component", {}).get("form", {})
    for slot in ("background", "border", "content"):
        for state, val in flat_leaves(form.get("color", {}).get(slot, {})):
            out.append((f"--form-{slot}-{state}", val))

    # component.card
    card = ctx.get("component", {}).get("card", {})
    for slot in ("background", "border", "content"):
        for state, val in flat_leaves(card.get("color", {}).get(slot, {})):
            out.append((f"--card-{slot}-{state}", val))
    h = card.get("image", {}).get("dimension", {}).get("height", {})
    if isinstance(h, dict) and "$value" in h:
        out.append(("--card-image-height", h["$value"]))
    pad = card.get("spacing", {}).get("padding", {})
    for axis, val in flat_leaves(pad):
        out.append((f"--card-padding-{axis}", val))
    tag_pad = card.get("tags", {}).get("spacing", {}).get("padding", {})
    if isinstance(tag_pad, dict) and "$value" in tag_pad:
        out.append(("--card-tags-padding", tag_pad["$value"]))
    for k, v in flat_leaves(card.get("tags", {}).get("borderRadius", {})):
        out.append((f"--card-tags-radius-{k}", v))

    return out


def flat_leaves(node, prefix=""):
    """Yield (kebab-path, $value) for every leaf token under node."""
    if not isinstance(node, dict):
        return
    if "$value" in node:
        yield (prefix.rstrip("-"), node["$value"])
        return
    for k, v in node.items():
        nxt = f"{prefix}{kebab(k)}-" if prefix else f"{kebab(k)}-"
        yield from flat_leaves(v, nxt)


def flatten(node, prefix=""):
    """Like flat_leaves but for color.* sub-trees (handles utility.*)."""
    if not isinstance(node, dict):
        return
    if "$value" in node:
        yield (prefix.rstrip("-"), node["$value"])
        return
    for k, v in node.items():
        nxt = f"{prefix}{kebab(k)}-" if prefix else f"{kebab(k)}-"
        yield from flatten(v, nxt)


# ---------- emit ----------
UNRESOLVED_FALLBACK = {
    "--color-background-muted-soft": "#f5f5f5",  # golf has no offWhite scale
}


def emit_block(selector, pairs, indent="  "):
    lines = [f"{selector} {{"]
    seen = set()
    for name, val in pairs:
        if name in seen:
            continue
        seen.add(name)
        if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
            fallback = UNRESOLVED_FALLBACK.get(name, "inherit")
            lines.append(f"{indent}{name}: {fallback}; /* unresolved ref: {val} */")
            continue
        lines.append(f"{indent}{name}: {val};")
    lines.append("}")
    return "\n".join(lines)


def main():
    golf = build_brand("golf")
    mini = build_brand("mini-golf")

    golf_vars = collect_vars(golf)
    mini_vars = collect_vars(mini)

    # diff: only emit overrides in mini-golf that differ
    golf_map = dict(golf_vars)
    mini_overrides = [(k, v) for k, v in mini_vars if golf_map.get(k) != v]

    # viewport overlays
    golf_small = build_viewport_overlay("golf", "small")
    mini_small = build_viewport_overlay("mini-golf", "small")
    small_pairs = []
    for k, v in flat_leaves(golf_small):
        small_pairs.append((f"--font-size-{k}", v))

    mini_small_pairs = []
    for k, v in flat_leaves(mini_small):
        mini_small_pairs.append((f"--font-size-{k}", v))

    out = ["/* tokens.css — generated from ./tokens. Do not hand-edit. */", ""]
    out.append(emit_block(":root", golf_vars))
    out.append("")
    out.append(emit_block('[data-brand="mini-golf"]', mini_overrides))
    out.append("")
    out.append("@media (max-width: 960px) {")
    out.append(emit_block("  :root", small_pairs, indent="    "))
    same = dict(small_pairs) == dict(mini_small_pairs)
    if not same:
        out.append("")
        out.append(emit_block('  [data-brand="mini-golf"]', mini_small_pairs, indent="    "))
    out.append("}")
    out.append("")

    # typography utility classes — composite styles
    typo_names = list(golf.get("semantic", {}).get("typography", {}).keys())
    out.append("/* typography composites — apply as a single class */")
    for name in typo_names:
        out.append(f".text-{name} {{")
        out.append(f"  font-family: var(--typography-{name}-font-family);")
        out.append(f"  font-weight: var(--typography-{name}-font-weight);")
        out.append(f"  font-size: var(--typography-{name}-font-size);")
        out.append(f"  line-height: var(--typography-{name}-line-height);")
        out.append(f"  letter-spacing: var(--typography-{name}-letter-spacing);")
        out.append("}")
    out.append("")

    OUT.write_text("\n".join(out))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(golf_vars)} golf vars, {len(mini_overrides)} mini-golf overrides)")


if __name__ == "__main__":
    main()
