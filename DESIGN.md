# Design

The world is **The Annotated Edition**: a wide-margin critical edition drawn by
a ruling engine. The course document stays printed text on unbleached paper;
everything the reader adds — an explanation, a kept highlight, a citation — hangs
in the margin beside the line it came from. Product truth lives in
[`PRODUCT.md`](PRODUCT.md).

It was chosen against six alternatives, including a Zettelkasten slip box and a
phosphor terminal, on two axes: whether the audience recognises the world, and
whether it makes the product clearer. A student's own textbook wins both — and
the product's core mechanism, an explanation cited to a document and a page, is
already a margin apparatus.

## Laws

These are the rules the world is built on. Breaking one is a defect, not a
variation.

1. **Colour never enters the text column.** All colour lives on rails,
   brackets, edges and marks. The reading field is ink on paper.
2. **One reserved colour.** Rubric vermilion marks the reader's own work and the
   active position — a kept highlight, the current page, a missed answer, focus.
   It is never decoration and never a brand flourish.
3. **The ground is committed.** Unbleached paper owns every viewport. No white
   cards floating on grey, and no default `#fff`.
4. **States are printed marks.** A control is a hairline rectangle at rest and
   fills with rubric when pressed. No radius anywhere, no shadow, no glass.
5. **The apparatus is small caps.** Labels, keys, counts and metadata are
   uppercase at 11px with wide tracking, in slate. Never sentence case, never
   body size.
6. **The source material is the hero.** Chrome gets the smallest share of the
   viewport that still works.

## Palette

| Token | Value | Use |
|---|---|---|
| `paper` | `#f3eee3` | The ground, everywhere |
| `paper-lift` | `#f8f4ec` | The annotation margin and code blocks |
| `paper-deep` | `#ece5d6` | Inline code, loading marks |
| `ink` | `#1a1a1a` | Body text, headings, the graph's concepts |
| `slate` | `#57534c` | Apparatus, secondary prose, documents in the graph |
| `ash` | `#a39c8f` | Inactive keys, placeholders, ordinals |
| `rubric` | `#c23a2a` | The reader's own marks and the active position |
| `rubric-deep` | `#98291c` | Rubric text on paper, where contrast needs it |
| `rule` | `#cfc6b4` | Hairlines |
| `rule-strong` | `#a89e8b` | Control borders, scrollbar thumb |

## Type

One serif carries everything: **Source Serif 4**, self-hosted through
`next/font`. **IBM Plex Mono** is reserved for code and nothing else — mono as a
costume for "technical" is banned.

| Step | Size | Use |
|---|---|---|
| `apparatus` | 11px, `0.12em` tracking, uppercase | Labels, keys, metadata, counts |
| `fine` | 13px | Margin notes, options, secondary prose |
| `body` | 17px | Reading text |
| `lead` | 20px | Section leads, user questions, node titles |
| `display` | 34px | Page titles |

Fixed rem steps, not fluid: the reader sits at a consistent viewing distance and
a heading that shrinks inside a panel looks worse, not better. Prose holds a
62–68ch measure.

## Components

- `.apparatus` — the small-caps label style.
- `.detent` — a ruled control. Hairline at rest, `border-color: ink` on hover,
  filled rubric when pressed or `data-state="on"`, ash when disabled.
- `.bracketed` — a rubric hairline down the left edge, bracketing a note back
  into the line it belongs to. Used for quotes, reasons, explanations.
- `.ruled-block` — a hairline block with corner detents, for errors and
  instructional blocks.
- `.tabular` — tabular numerals, on every key, count and score.
- `.no-scrollbar` — the nav strip only.

All of these live in `@layer components` so utilities can still override them.
Defining them outside the layer silently beat every `text-*` utility, which is
how the first build shipped an unreadable active page key.

## Composition

The reader is the lead surface and the shape everything else inherits:

```
nav strip (keyed, hairline cells)
─────────────────────────────────────────────
document header: title + topic + way out
─────────────────────────────────────────────
        page at reading measure  │ keys │ annotation margin
```

Below `lg`, the margin becomes a band under the document rather than a column
beside it — a fixed 22rem column starves a phone of the thing it came for. The
key rail hides below `md`.

Other surfaces are ruled lists, not card grids: rows separated by hairlines,
numbered in the apparatus, with the row's own content carrying the weight.
Cards as a page scaffold are banned here.

## Motion

150–250ms colour transitions on controls, and nothing else. No entrance
choreography: the reader arrives in a task. `prefers-reduced-motion` drops
everything to 0.01ms.

## Browser surfaces

Selection is rubric at 22%, the caret is rubric, the focus ring is a rubric
hairline at 2px offset, and the scrollbar is `rule-strong` on paper in both the
standard and WebKit syntaxes. These ship with the design, not with the browser.

## Light only

There is no dark mode, deliberately. The world is paper, and the ground is warm
enough for long sessions. A dark variant would be a different world, not a
setting.
