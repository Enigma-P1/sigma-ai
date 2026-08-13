# Security

## The threat model, plainly

Sigma AI is a local desktop app. Your projects are folders on your own
machine; nothing leaves it unless you turn on the optional AI advisor.

The app has two parts: the window you see, and a statistics engine it
starts on `127.0.0.1` (your machine only — it never listens for other
computers). Requests from the app's own window are allowed; requests
carrying any other website's origin are refused, so a web page you happen
to have open cannot read or delete your projects while the app runs.

What this design deliberately does **not** defend against is other
software already running on your machine with your privileges. A local
process could call the engine — and could equally just read the project
folders off disk, which is why the engine adds no password: it would be a
lock on a door standing next to an open window. If your machine is
shared or compromised, Sigma AI's data is as exposed as any of your
documents.

## The advisor key

If you enable the optional LLM advisor, your API key is stored **in plain
text** in `settings.json` in the app's data folder. The settings screen
says so before you save it. Moving it into the operating system's
credential store is planned; until then, treat that file like the key
itself.

## Data provenance

Imported datasets are content-addressed (SHA-256) and never edited in
place — corrections create a new version with recorded lineage. Externally
supplied identifiers (project, dataset, image, tool ids) are validated
before they touch the filesystem, and resolved paths are checked to stay
inside the projects folder.

## Reporting

Open a GitHub issue, or email the maintainer, for anything you believe is
a vulnerability. There is no bounty; there is gratitude and a fast fix.
