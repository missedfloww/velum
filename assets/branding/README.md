# Velum Branding Assets

This directory holds the brand assets shipped with Velum. The set is
deliberately small: Velum is a CLI Python package, not a website or a
mobile app, so it does not need favicons, PWA icons, or iOS/Android home-
screen art. The runtime UI uses a single SVG mark bundled with the wheel
at `src/velum/frontend/static/mark.svg`.

## Files

| File | Size | Use |
|------|------|-----|
| `banner.png` | 1280×320 | README dark-mode header |
| `banner-light.png` | 1280×320 | README light-mode header |
| `og-image.png` | 1280×640 | GitHub repo social preview (upload via *Settings → Social preview*) |
| `screenshot.png` | — | Poster frame for the README demo `<video>` (shows before play) and standalone fallback for viewers that strip video |

The README's inline demo video is hosted on GitHub's `user-attachments` CDN
(uploaded once via the issue-comment drag-and-drop trick — GitHub strips
`<video src="repo/path">` tags from raw READMEs but allows them when the
`src` is a `user-attachments` URL). The MP4 source for the demo lives only
on that CDN, not in the repo.

The runtime mark lives at `src/velum/frontend/static/mark.svg`. It is a
single SVG with embedded `prefers-color-scheme` styles so the fill
switches between white on dark surfaces and slate (`#1E293B`) on light.

## Brand tokens

| Token | Hex | Use |
|-------|-----|-----|
| Slate | `#0F172A` | Dark-mode background |
| Slate dark | `#1E293B` | Light-mode mark + body text |
| Slate light | `#94A3B8` | Secondary text (taglines, captions) |
| White | `#FFFFFF` | Mark + headings on dark |

Velum's mark is a sibling of the GeminaVox brand: thin uniform white line
strokes on deep slate, symmetric dual-metaphor composition (central
vertical element flanked by horizontal elements). Any future brand work
should respect this signature.
