# Field notes — things observed while actually using the installed app

Rough-edge log from real use of a shipped build, kept separate from the
bug tracker on purpose: these are not crashes and not wrong math. They are
places where the app is correct but unhelpful. Each entry says what was
observed, why it happens, and what it would take to fix — so a future
build can batch them instead of spending an installer build on each.

Ordered newest first.

---

## 2026-08-09 — No forward navigation after saving a tool

**Observed (Shawn, v0.1.2, first run through T-01):** Filled in the Project
Picker, hit **Save**. Got "All checks pass — route matches your answers."
Then nothing. The next tool unlocks in the left-hand rail, but the screen
stays on the tool just finished and never says "go here next." Had to work
out that the rail was the way forward.

> "when I get done with the zero one, I hit save, and it says all checks
> pass, route matches your answers, and then that's it. It doesn't take me
> to the next step, but it does open it up on the left hand. Maybe it's
> just a note. You know, click t-02 or something if it doesn't
> automatically go to it."

**Why:** save and navigation are deliberately decoupled — the tool screens
save in place so you can re-read the checks strip against what you typed,
and the rail is the single source of truth for what is unlocked. Nothing
ever proposed the next step because the rail was assumed to be self-evident.
It is self-evident to whoever built it, which is not the test.

**Fix (needs a build):** on a passing save, add a next-step affordance to
the verdict banner — "Next: T-02 COPQ →" as a button that navigates, with
the tool name resolved from the same route the picker produced, so it
follows quick-path vs full-DMAIC correctly. Do not auto-navigate; that
would yank the checks strip away before it has been read. Cheap, and it is
the difference between a guided product and a filing cabinet.

**Status:** logged, not built. Batch with the next UI build.

---

## 2026-08-09 — A dropped-in project can't be found from the Open screen

**Observed (Shawn, v0.1.2):** Unzipped `examples/coffee-bar-example-project.zip`
into the projects folder, restarted as the README said, and the worked
example was not in the *Open a project* list. Only the project he had
created himself was there.

> "Your instructions are not clear enough. It says restart, which I did.
> Open a project, and then just an arrow to coffee bar hyphen worked
> example. Is that what I paste in here? How do I find it? I don't even
> understand."

**Why:** the list on that screen is a recently-opened history in
localStorage (`app/project/recentProjects.ts`), not a scan of the projects
folder — the engine has no "list all projects" endpoint, which
`OpenProjectScreen.tsx` says in a comment. A project placed on disk by
hand has never been opened on that machine, so by construction it cannot
appear. The instructions were written against how the folder works, not
how the screen works.

**Fixed in docs the same day:** `examples/README.md` now says to type
`coffee-bar-example` into **Or open by project ID** and states plainly that
it will not appear in the list above, and why.

**Fix (needs a build):** give the engine a `GET /projects` that lists the
folders under the projects root with their names, and have the Open screen
show *Found on this machine* alongside *Recently opened*. Then a
drop-in project is visible without anyone knowing an ID. The localStorage
list stays useful for ordering by recency and for surviving a moved folder.

**Status:** docs fixed; engine endpoint logged, not built.
