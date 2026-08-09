# Installing Sigma AI on Mac

This guide takes you from nothing to a working Sigma AI on a Mac. No Python,
no Terminal required for the install itself — the app carries its own
statistics engine inside.

## 1. Download and install

1. Sign in to GitHub (this is a private repo, so downloads need an account
   with access).
2. Go to the repo's **Releases** page — click **Releases** in the right-hand
   sidebar of the repo home page, or add `/releases` to the repo URL.
3. On the newest release, under **Assets**, download the disk image, named
   like `Sigma AI_0.1.0_arm64.dmg` — the last part is the processor it was
   built for (`arm64` = Apple silicon, which is what CI currently builds;
   check it matches your Mac).
4. Open the `.dmg` and drag **Sigma AI** into your **Applications** folder,
   then eject the disk image.

(Installers are also parked in the **Actions** tab under **Artifacts** on
every push to `main` — that's a developer fallback, not the place to go; the
Releases page above is the real download.)

## 2. First launch — getting past the unsigned-app warning

**The first open will be blocked.** This app is not code-signed or notarized
— the project does not (yet) pay for an Apple Developer identity — so
Gatekeeper (macOS's app-vetting layer) reports that it "could not verify"
the app. That is the absence of a signature, not a malware finding. The
standard route past it:

1. Double-click Sigma AI once and let macOS block it (click **Done**, not
   "Move to Trash").
2. Open **System Settings → Privacy & Security**, scroll down to the message
   about Sigma AI, and click **Open Anyway**, then confirm.

On older macOS versions, right-clicking the app and choosing **Open** offers
the same "Open Anyway" escape directly. If you would rather not open
unsigned software at all — a reasonable position — run the app from source
instead (see the README's Quickstart); nothing about the suite requires the
prebuilt bundle.

## 3. What you should see

Once open, the app shows the **home screen**: create a project (name it, the
app suggests a folder-safe id) or open an existing one. In the background it
has started its own statistics engine — a small local program (the
"sidecar") that does all the math, listening only on your own machine
(`127.0.0.1`, port 8756), never on the network.

To confirm the engine is alive, click **Diagnostics** (top right): it shows
engine health and runs a live smoke check — the engine computes the mean and
standard deviation of a NIST reference dataset and compares them against the
certified values, on your machine, right then.

**Where your work lives:** every project is a plain folder of JSON files at
`~/.sigma-ai/projects/<project-id>` — portable, versioned on every save, and
readable without the app. Back up or move a project by copying its folder.

## 4. Optional: connect the AI advisor

Layer 1 (everything above) needs no key and no internet. If you want the AI
advisor (Layer 2), you need an Anthropic API key:

1. Create a key at the Anthropic console (console.anthropic.com — paid,
   pay-per-use).
2. In Sigma AI, click **Advisor settings** (top right), paste the key, and
   save. Leave the field empty and the app simply stays a fully working
   offline suite.

The settings screen states exactly what the advisor sends, and the same
statement belongs here, word for word:

> The advisor (Layer 2) sends nothing until you actually use it. When you ask
> it something, the current artifact goes in full, along with its computed
> results and pre-score findings; most modes also send short, code-generated
> summaries of your project's other saved artifacts, so the advisor can
> reference them or ask to see one in full. "Check my claims" additionally
> sends a summary of every dataset you've imported into this project,
> including up to 3 sample values per column. Don't put customer names or
> other sensitive identifiers in artifact text or imported datasets. Your API
> key is stored in plain text in settings.json on this machine -- it is not
> encrypted.

(That `settings.json` sits next to your projects, at
`~/.sigma-ai/projects/settings.json`.)

## 5. Troubleshooting

**"Sigma AI can't be opened" / "could not verify" dialogs.** Expected for an
unsigned app — use the **Privacy & Security → Open Anyway** route in step 2.
If macOS says the app is *damaged*, the download's quarantine flag is
tripping Gatekeeper's strictest response; re-download first, and only if you
trust the source and know what you're doing, clear the flag in Terminal:
`xattr -d com.apple.quarantine "/Applications/Sigma AI.app"`.

**Security software quarantines the app's engine.** The statistics engine
inside the app bundle (`sigma-engine`) is packaged with PyInstaller, which
bundles a Python program into one executable — some security products flag
any such unsigned binary on reputation alone. The symptom: the app opens but
every tool reports the engine unreachable. If you trust the source (this
repo's own CI), restore the file and exclude the app; otherwise run from
source.

**Port conflict — app opens but tools can't reach the engine.** The engine
listens on port 8756 on your own machine, fixed in this version. If another
program holds it, the engine can't start. Check in Terminal:

```bash
lsof -nP -iTCP:8756 -sTCP:LISTEN
```

If something is listed, quit that program (or reboot) and reopen Sigma AI.
**Diagnostics** (top right) confirms when the engine is back.

**Where to report anything else:** open an issue on the GitHub repo with the
Diagnostics screen's output — it names the engine version and health state,
which is most of what a bug report needs.
