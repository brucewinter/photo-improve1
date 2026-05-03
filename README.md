# photo-improve

A local pipeline for restoring old scanned photos. Free / open-source AI models, CPU-friendly defaults, optional Google Photos sync.

Status: **v0.2** — auto-levels, classical enhancement, **and Gemini 2.5 Flash Image (Nano Banana) restoration** work end-to-end. Local AI steps (Real-ESRGAN, GFPGAN, colorization) and Google Photos sync are stubbed with clean interfaces, ready to be filled in.

## What it does

Given an input folder of old scanned photos, produce a clean output folder of restored copies. Originals are never modified. Pipeline steps (each independently toggleable in `config.yaml`):

1. **Upscale + denoise** — Real-ESRGAN (planned)
2. **Face restoration** — GFPGAN (planned)
3. **Colorization** — DeOldify or similar (planned, B&W only)
4. **Classical enhance** — white balance, CLAHE, bilateral denoise, unsharp mask, saturation (working)
5. **Auto-levels** — percentile-based histogram stretch (working)

Plus optional **Google Photos sync** — download a named album, restore, upload restored copies into a new album. (Planned.)

For the manual-tools workflow that this project automates, see [Restore-Old-Scanned-Photos.md](./Restore-Old-Scanned-Photos.md).

## Quickstart

```powershell
# From C:\Apps\photo-improve1
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# Copy the example config and tweak as needed
copy config.example.yaml config.yaml

# Drop scanned photos into input/, then:
photo-improve run

# Or to see what would happen without processing:
photo-improve --dry-run run
```

Restored copies appear in `output/` with the same filenames.

## Recommended setup: Gemini-powered restoration

For best results, enable the `gemini_restore` step. It calls Google's
**Gemini 2.5 Flash Image** model (a.k.a. "Nano Banana") for AI restoration —
matches what you'd get from the Gemini app, but automated over your folder.

```powershell
# 1. Install the optional Gemini SDK
pip install -e ".[gemini]"

# 2. Get a free API key at https://aistudio.google.com/apikey
setx GEMINI_API_KEY "your-key-here"
# Open a new PowerShell window so the env var is visible.

# 3. In config.yaml, flip `enabled: true` on the gemini_restore step,
#    and (optionally) flip `enabled: false` on enhance and levels —
#    Gemini does enough on its own that the classical steps may be redundant.

photo-improve run
```

Cost: Gemini's free tier easily covers tens of photos. Beyond that it's a
fraction of a cent per image. See https://ai.google.dev/pricing for current
rates.

## CLI

```
photo-improve run              # process input/ → output/
photo-improve run --dry-run    # show plan, don't process
photo-improve watch            # daemon mode (planned, stubbed)
photo-improve sync             # google photos sync (planned, stubbed)
photo-improve --version
```

## Project layout

```
photo-improve1/
├── README.md
├── Restore-Old-Scanned-Photos.md   manual-workflow reference
├── pyproject.toml                  packaging + console script
├── requirements.txt                pinned deps (mirrors pyproject)
├── config.example.yaml             example config
├── photo_improve/                  package
│   ├── cli.py                      argparse entry point
│   ├── config.py                   YAML config loader + validator
│   ├── logging_setup.py            structured logging
│   ├── pipeline.py                 step orchestrator
│   ├── steps/
│   │   ├── base.py                 Step protocol
│   │   ├── levels.py               WORKING: auto-levels
│   │   ├── upscale.py              STUB: Real-ESRGAN
│   │   ├── face_restore.py         STUB: GFPGAN
│   │   └── colorize.py             STUB: DeOldify
│   ├── google_photos/              STUB: OAuth + album sync
│   └── watcher.py                  STUB: folder watcher
├── tests/                          pytest tests
├── input/                          drop photos here (gitignored)
└── output/                         restored copies (gitignored)
```

## Roadmap

**v0.1 (current scaffold)**
- Project structure, packaging, config, logging
- CLI with `run` subcommand and `--dry-run`
- Working auto-levels step
- AI steps stubbed (act as no-op pass-through with a warning log)
- Google Photos and watcher stubbed
- Tests for config and levels

**v0.2 — Real-ESRGAN integration**
- Add `realesrgan` pip package
- Wire `steps/upscale.py` to call it on CPU with the `realesr-general-x4v3` model
- Cache model weights under `models/` (gitignored)

**v0.3 — GFPGAN face restoration**
- Add `gfpgan` pip package
- Wire `steps/face_restore.py` with strength slider in config

**v0.4 — Colorization**
- Pick: DeOldify (heavier) vs ddcolor (lighter, also good)
- Wire `steps/colorize.py`; only enable on photos detected as B&W (heuristic: low color saturation)

**v0.5 — Watcher mode**
- Add `watchdog` dep
- `photo-improve watch` processes new files in `input/` as they appear

**v0.6 — Google Photos sync**
- OAuth setup with Google's installed-app flow
- `photo-improve sync --album "Old Scans" --dest "Old Scans — Restored"`
- Download → process → upload to new album

## Notes on running on CPU

All chosen models work on CPU. Expect roughly:
- Real-ESRGAN 2x: 15–40s per photo
- GFPGAN: 5–15s per photo
- DeOldify: 10–30s per photo

For ~50 photos, that's still under an hour total even with everything enabled.

## Development

```powershell
# Run tests
pytest

# Run with verbose logs
photo-improve run --log-level DEBUG
```
