<p align="center">
  <img src="https://raw.githubusercontent.com/missedfloww/velum/main/assets/branding/banner.png" alt="Velum" width="640" />
</p>

<p align="center">
  <strong>Local-first PII redaction. One command. No cloud.</strong>
</p>

<p align="center">
  <a href="#install"><img src="https://img.shields.io/badge/install-uvx%20velum--pii-6366F1" alt="uvx velum-pii" /></a>
  <a href="https://pypi.org/project/velum-pii/"><img src="https://img.shields.io/pypi/v/velum-pii?label=PyPI&color=6366F1" alt="PyPI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="Apache 2.0" /></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Windows | macOS | Linux" />
</p>

---

Velum redacts personally identifiable information from text without ever sending data to a remote server. Powered by OpenAI's open-source [privacy-filter](https://github.com/openai/privacy-filter) model running fully on your machine, with a deterministic regex backstop for high-risk credentials (AWS keys, GitHub tokens, OpenAI/Anthropic keys, Google API keys, Slack tokens).

## Install

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). Tested on Windows, macOS, and Linux against Python 3.11 and 3.12 in CI.

```bash
uvx velum-pii
```

That's it. The first run downloads the model (~600 MB, one time). The browser opens to `http://localhost:8501`.

> **Why `velum-pii` instead of `velum`?** The bare `velum` name on PyPI was already taken by an unrelated project template when this tool launched. The brand stays *Velum*; only the PyPI install identifier carries the suffix. The CLI command after install is still `velum`.

Velum runs on **CPU only** in v0.1.0 — PyTorch is installed from the CPU wheel index. Inference takes a couple of seconds for a paragraph on a modern laptop; long documents take proportionally longer. GPU support is not currently exposed.

## Demo

<p align="center">
  <a href="https://github.com/user-attachments/assets/7723aaee-5e7d-48ae-a9c6-1ac65ca9c73c">
    <img src="https://raw.githubusercontent.com/missedfloww/velum/main/assets/branding/screenshot.png" alt="Velum screenshot — click to watch the demo video" width="720" />
  </a>
</p>

> Click the screenshot above to watch the 1-minute demo video.

## What it detects

- Names, emails, phone numbers, addresses, dates, URLs
- Account numbers (SSN, bank, brokerage, insurance, medical record IDs)
- Secrets (passwords, crypto wallets, API keys, tokens)

The regex backstop guarantees credentials with distinctive prefixes are never missed even if the surrounding text tries to disclaim them:

| Pattern | Example |
|---|---|
| AWS access key ID | `AKIA...` |
| GitHub PAT (classic & fine-grained) | `ghp_...`, `github_pat_...` |
| OpenAI / Anthropic | `sk-...` |
| Google API key | `AIza...` |
| Slack token | `xoxb-...`, `xoxp-...` |

## Privacy

Velum never makes a network call after install. The backend listens only on `127.0.0.1`. CORS is locked to localhost. There is no telemetry. The full source is auditable in this repo.

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Contributing

This is a solo project at the moment. Issues and PRs welcome once it's past v0.1.0.

## Acknowledgements

Velum wraps the [openai/privacy-filter](https://huggingface.co/openai/privacy-filter) model and its companion [opf](https://github.com/openai/privacy-filter) Python package, both released by OpenAI under the Apache License 2.0. Velum is an independent project and is not affiliated with, sponsored by, or endorsed by OpenAI. See [NOTICE](NOTICE) for full attribution.

## License

Apache 2.0 — see [LICENSE](LICENSE).
