# Changelog

All notable changes to Velum are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.4] - 2026-05-10

Local-first compliance fix surfaced by the same WSL2 Ubuntu smoke run that
shipped v0.1.3.

### Fixed
- Streamlit's first-run welcome message no longer surfaces. The
  `--browser.gatherUsageStats false` flag passed to `streamlit run` already
  disabled telemetry uploads, but Streamlit still printed an interactive
  "Welcome to Streamlit! ... please enter your email address" prompt on the
  first launch because that prompt is gated by the existence of
  `~/.streamlit/credentials.toml`, not by the telemetry flag. The launcher
  now pre-creates that file with an empty email so Streamlit treats the user
  as already onboarded. The behaviour is idempotent — if the file already
  exists with user-provided content, it is left untouched.

## [0.1.3] - 2026-05-10

Install UX fix discovered by first cross-platform smoke test on WSL2 Ubuntu.

### Fixed
- `uvx velum-pii` now works directly instead of failing with `An executable
  named 'velum-pii' is not provided by package 'velum-pii'`. The package
  installs a `velum` executable, but `uvx` looks for an executable matching
  the package name by default. Added `velum-pii` as a second console-script
  entry mapped to the same `velum.cli:main` function. Both commands behave
  identically; users who already learned the workaround (`uvx --from
  velum-pii velum`) keep working too.

## [0.1.2] - 2026-05-10

Documentation patch — no functional or packaging changes. Supersedes v0.1.1
on TestPyPI (v0.1.1 was never promoted to real PyPI).

### Fixed
- README images (header banner, demo video poster, screenshot fallback link)
  now use absolute `raw.githubusercontent.com` URLs so they render on PyPI's
  project page. The previous repo-relative `<img src="assets/...">` worked on
  GitHub but resolved to 404s on `pypi.org/project/velum-pii/`.
- Header now uses a single banner instead of paired dark/light banners. PyPI's
  Markdown renderer ignores the GitHub-only `#gh-dark-mode-only` /
  `#gh-light-mode-only` URL fragments, so both banners were rendering stacked
  on the PyPI project page. The single banner has a self-contained dark
  background and reads fine on both GitHub themes.
- Demo section replaced the inline `<video>` element with a click-through
  screenshot linking to the video. PyPI's Markdown sanitizer strips `<video>`
  tags entirely, leaving only the fallback text — the Demo section appeared
  empty on `pypi.org`. The click-through image renders on both PyPI and
  GitHub; the trade-off is that GitHub no longer plays the video inline (a
  click still opens it on the user-attachments CDN).

## [0.1.0] - 2026-05-10

First public release.

### Added
- One-command install via `uvx velum-pii`. The CLI command after install is
  `velum` (the `-pii` suffix is only on the PyPI distribution name because
  the bare `velum` name was already squatted by an unrelated project).
- FastAPI backend (port 8000) and Streamlit frontend (port 8501) launched
  by a single `velum` CLI entry point. Both bind to `127.0.0.1` only.
- Detection of names, emails, phone numbers, addresses, dates, URLs,
  account numbers, and secrets via OpenAI's open-source privacy-filter model.
- Deterministic regex backstop for AWS, GitHub, OpenAI/Anthropic, Google,
  and Slack credentials.
- Span boundary post-processing to trim absorbed punctuation.
- OS-adaptive light/dark theme.
- Auditable, fully local, no telemetry.

### Internal / distribution
- The OpenAI privacy-filter runtime (`opf`) is vendored under
  `src/velum/_vendor/opf/` (Apache 2.0 — see `LICENSE-OPF` and `NOTICE`).
  `pyproject.toml` no longer declares a URL dependency, so the wheel's
  `Requires-Dist` lines are all standard PyPI references, which is what
  PyPI requires. `uvx velum-pii` resolves end-to-end from PyPI alone.

### Known limitations
- The full end-to-end install + model-load + UI flow has been hand-verified
  on Windows. CI passes on Ubuntu, macOS, and Windows (Python 3.11 and 3.12),
  and the codebase has no platform-specific paths, so Linux and macOS
  *should* work — but a real human has not yet run the tool end-to-end on
  those platforms. If you hit a bug on Linux or macOS, please open an issue
  with your OS, Python version, and the full traceback.
- First run downloads the privacy-filter model (~600 MB). Allow a few
  minutes on a typical home connection; subsequent runs use the cached copy.
- CPU-only inference. GPU support is not exposed in v0.1.0.
