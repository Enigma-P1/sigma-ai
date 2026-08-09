# Installing Sigma AI on Windows

This guide takes you from nothing to a working Sigma AI on Windows. No
Python, no command line — the installer carries everything the app needs.

## 1. Download the installer

1. Sign in to GitHub (this is a private repo, so downloads need an account
   with access).
2. Go to the repo's **Releases** page — click **Releases** in the right-hand
   sidebar of the repo home page, or add `/releases` to the repo URL.
3. On the newest release, under **Assets**, download one of the Windows
   installers (both produce the same app):
   - the **`.msi`** — the standard Windows installer package. Pick this one if
     unsure.
   - the **`.exe`** (NSIS setup program) — useful if your machine's policy
     blocks `.msi` files.

That's the whole download. (Installers are also built on every push to `main`
and parked in the **Actions** tab under **Artifacts** — that's a developer
fallback, not the place to go; the Releases page above is the real download.)

## 2. Run the installer

Double-click the `.msi` (or the setup `.exe`) and click through.

**You will see a blue "Windows protected your PC" warning.** That is
SmartScreen reacting to an app that is not code-signed — this project does
not (yet) buy a signing certificate, so Windows has no publisher identity to
verify and warns on principle. It is not a malware detection. To proceed:
click **More info**, then **Run anyway**. If you'd rather not, that is a
reasonable choice — you can instead run the app from source (see the README's
Quickstart), where nothing is pre-built.

## 3. First launch — what you should see

Start **Sigma AI** from the Start menu. Two things happen:

1. The app window opens on the **home screen**: create a project (name it,
   the app suggests a folder-safe id) or open an existing one, with a
   recent-projects list once you have any.
2. In the background, the app starts its own statistics engine — a small
   local program (the "sidecar") that does all the math. It listens only on
   your own machine (`127.0.0.1`, port 8756) and is never reachable from the
   network. You don't manage it; it starts with the app and stops when you
   close the window.

To confirm the engine is alive, click **Diagnostics** (top right). It shows
the engine's health and runs a live smoke check: the engine computes the mean
and standard deviation of a NIST reference dataset and compares them against
the certified values. If that page says the computed and certified values
match, the whole stats engine is provably running on your machine.

**Where your work lives:** every project is a plain folder of JSON files at
`C:\Users\<you>\.sigma-ai\projects\<project-id>` — portable, versioned on
every save, and readable without the app. Back up or move a project by
copying its folder.

## 4. Optional: connect the AI advisor

Layer 1 (everything above) needs no key and no internet. If you want the AI
advisor (Layer 2), you need an Anthropic API key:

1. Create a key at the Anthropic console (console.anthropic.com — paid,
   pay-per-use).
2. In Sigma AI, click **Advisor settings** (top right), paste the key, and
   save. The advisor panel on every tool screen comes alive; leave the field
   empty and the app simply stays a fully working offline suite.

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
`C:\Users\<you>\.sigma-ai\projects\settings.json`.)

## 5. Troubleshooting

**"Windows protected your PC" / SmartScreen warning.** Expected — the app is
unsigned (see step 2). **More info → Run anyway**, or use the from-source
route instead.

**Antivirus quarantines or deletes the app's engine.** The statistics engine
is packaged with PyInstaller (a standard tool that bundles a Python program
into an `.exe`), and some antivirus products flag *any* PyInstaller-built
executable on reputation alone — unsigned + unknown = suspicious to them.
The symptom: the app window opens but every tool reports the engine as
unreachable, and a `sigma-engine.exe` shows up in your AV's quarantine. If
you trust the source (you downloaded from this repo's own CI), restore the
file and add the app's install folder to the AV's exclusions. If you don't
want to allowlist anything, run from source instead — same code, no bundled
binary.

**Port conflict — app opens but tools can't reach the engine.** The engine
listens on port 8756 on your own machine, and that number is fixed in this
version. If another program already occupies it, the engine can't start.
Check with PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8756 -State Listen
```

If something is listed, close that program (or reboot) and start Sigma AI
again. `Diagnostics` (top right) confirms when the engine is back.

**Where to report anything else:** open an issue on the GitHub repo with the
Diagnostics screen's output — it names the engine version and health state,
which is most of what a bug report needs.
