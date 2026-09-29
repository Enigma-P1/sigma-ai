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

## GitHub Actions and AI-agent guardrail

Content supplied by outside contributors — including issue titles and
bodies, comments, pull-request titles and bodies, review comments, commit
messages, uploaded text, and code from forks — is **untrusted input**.

Do not add a workflow that sends that input directly to an AI/LLM agent
that has repository write access, a write-capable `GITHUB_TOKEN`, API
keys, deployment credentials, signing credentials, or any other secret.

In particular:

- Do not trigger a privileged AI agent directly from `issue_comment`,
  `issues`, `pull_request_review_comment`, or similar public-input events.
- Avoid `pull_request_target` for workflows that execute, interpret, or
  hand attacker-controlled content to an agent.
- Any AI analysis of public contributor content must run with
  `permissions: contents: read` (or less), with no repository/environment
  secrets exposed and no write-capable external tool credentials.
- Keep untrusted analysis and privileged actions in separate jobs or
  workflows. A maintainer must explicitly approve the transition from
  analysis to any write/deploy/release action.
- Never rely on prompt wording, escaping, or "ignore malicious
  instructions" text as the security boundary. The boundary is permissions,
  secret isolation, and an explicit trusted approval step.
- If an agentic workflow is added later, review its event trigger,
  permissions, secrets, checkout target, and tool capabilities before
  enabling it on a public repository.

This rule is intentionally stricter than normal CI because an AI agent can
interpret attacker-controlled natural language as instructions.

## Reporting

Open a GitHub issue, or email the maintainer, for anything you believe is
a vulnerability. There is no bounty; there is gratitude and a fast fix.
