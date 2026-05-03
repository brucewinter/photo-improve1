# Restoring Old Scanned Photos — Free Workflow

A step-by-step playbook for cleaning up old scanned photos in a Google Photos album. Originals are never modified — every output is a copy that gets re-uploaded into a new album.

## The pipeline at a glance

1. **Export** the album from Google Photos to your PC.
2. **Restore** locally using free AI tools (sharpen, denoise, fix faces, fix levels, optionally colorize).
3. **Re-upload** the restored copies into a new album in Google Photos.

Total time for ~50 photos: roughly an hour of hands-on work plus some unattended processing.

---

## Step 1 — Export the album

Use Google Takeout, which lets you pick a single album:

1. Go to https://takeout.google.com
2. Click **Deselect all**, then scroll to **Google Photos** and check it.
3. Click **All photo albums included** and pick just the album you want.
4. Choose **.zip**, **2 GB max**, **Send download link by email**.
5. Wait for the email (usually a few minutes for under 50 photos), download, unzip.

Put the unzipped photos in a working folder, e.g. `C:\Users\bruce\Pictures\Restore\input\`.

> Tip: Also create `C:\Users\bruce\Pictures\Restore\output\` for the restored copies. Keeping inputs and outputs in separate folders makes it impossible to accidentally overwrite an original.

---

## Step 2 — Restore locally (free tools)

You'll use two or three tools depending on what each photo needs. All are free and run on Windows.

### A. Upscayl — sharpen, denoise, upscale (the workhorse)

**What it does:** AI upscaling and detail recovery. Has a built-in batch mode and several models tuned for different photo types.

- Download: https://upscayl.org (free, open-source, Windows installer)
- Recommended models for old scans:
  - **Remacri** or **Ultrasharp** — general-purpose, great on faded photos
  - **Digital Art** — only if a photo is very low-res / heavily damaged
- Settings to start with:
  - Scale: **2x** (4x is overkill for most scans and adds artifacts)
  - Output format: **PNG** (lossless; you can convert to JPG at the end)
  - Enable **Face Enhance** — this invokes GFPGAN for faces

Drop your `input` folder in, point output to `output`, click **Upscayl**. Walk away. Comes back to enhanced versions.

### B. GFPGAN / CodeFormer — when faces still need help

If Upscayl's face enhance isn't strong enough on a particular photo (very small or very damaged faces), use a dedicated face-restoration model via a free web demo:

- **GFPGAN** demo: https://huggingface.co/spaces/Xintao/GFPGAN
- **CodeFormer** demo: https://huggingface.co/spaces/sczhou/CodeFormer (often better on heavy damage; has a "fidelity" slider — 0.5 is a good default)

Upload one photo at a time, download the result. Use this only on photos where Upscayl's pass wasn't enough — it's per-photo and slow.

### C. Auto-levels & color correction

For faded, yellowed, or low-contrast photos, run an auto-levels pass. Two free options:

- **GIMP** (https://gimp.org) — open photo, then `Colors → Levels → Auto Input Levels`, and `Colors → Curves` for fine tuning. Good for hands-on per-photo work.
- **Built-in to Upscayl?** No — but the AI models do implicitly correct contrast somewhat. If photos still look flat after Upscayl, run them through GIMP's auto-levels as a final step.

### D. Colorize black-and-white photos

- **Palette.fm** (https://palette.fm) — free tier, very good results, browser-based, no install. Best free option for colorization in 2026.
- **DeOldify** demo: https://huggingface.co/spaces/PaddlePaddle/deoldify — open-source alternative.

Colorize *after* sharpening/denoising — colorizers work better on cleaner inputs.

---

## Recommended order of operations

For a typical faded color scan:
**Upscayl (with Face Enhance) → GIMP auto-levels → done.**

For a damaged B&W photo:
**Upscayl → CodeFormer on faces (if needed) → Palette.fm → GIMP auto-levels.**

Don't double-sharpen — running Upscayl twice or sharpening in GIMP after Upscayl creates halos and crunchy artifacts.

---

## Step 3 — Re-upload to Google Photos

1. Go to https://photos.google.com
2. Click **+ Create → Album**, name it something like "Family Photos — Restored 2026".
3. Drag your `output` folder's contents into the new album. Wait for upload.

Originals remain untouched in the original album; restored versions live in the new one.

> If you'd rather use the desktop uploader, install **Google Drive for Desktop** (which now handles Photos backup) and point it at your output folder.

---

## Quality checklist before re-uploading

For each batch, spot-check a handful side-by-side with the original:

- Faces look natural (not plasticky or "AI-smoothed" in a wax-figure way) — if they do, lower the face-restore strength or skip it on that photo.
- No haloing around high-contrast edges (sign of over-sharpening).
- Skin tones aren't pushed orange/red by colorization — Palette.fm has a "vibrant" vs "natural" toggle; "natural" is usually better.
- File sizes haven't ballooned absurdly (a 2x upscale to PNG can produce 10–20 MB files; convert to high-quality JPG at end if you care about Google Photos storage).

---

## If you want help running it

I can:

- Run Upscayl-equivalent processing on a sample photo if you drop one into the chat — useful as a sanity check before you install anything.
- Write a small Python script that does auto-levels and JPG conversion on a folder, if you'd rather automate the GIMP step.
- Walk through any step interactively (I can drive your screen through Cowork).

Just say the word.
