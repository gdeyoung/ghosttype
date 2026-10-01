# Launch kit — ghosttype

Everything here is a **draft for you to review and post yourself.** Nothing has
been published. I don't post under your name without you approving it first.

---

## 0. Read this before you post anything

**The blocker.** `main` currently points at the *old* upstream code — Russian UI,
bear icon, and the model-load crash. All the good work lives on `ghosttype-init`
behind a **draft** PR. If you share the repo link today, strangers land on the
broken version and bounce.

**Do this first, in order:**

1. Merge PR #1 (`ghosttype-init` → `main`), or mark the draft ready and merge.
2. Confirm `https://github.com/gdeyoung/ghosttype` shows the new README + ghost icon.
3. *Then* post.

**One loose end:** the History screenshot containing your real dictated text is
still in git *history* on the public branch. Zero watchers/stars/forks so far, so
exposure is small, but it is not zero. Say the word and I'll rewrite the branch
to purge it (destructive, force-push — your call).

---

## 1. Positioning

**The pitch, in one line:**

> The Voxtype experience on Windows — push-to-talk dictation that actually works
> on a laptop keyboard, and gets out of your way.

**Why this framing and not "a better WhisperWriter fork":**

Nobody needs another fork. People adopt a *capability*. The two upstream projects
have real audiences (savbell/whisper-writer: 1,103 stars; Voxtype: 1,581) but
neither is Windows-first, and neither is tuned for the two hardware problems that
actually block people on modern laptops.

**The wedge, honestly stated:**

| | Voxtype | ghosttype |
|---|---|---|
| Platform | Linux + macOS | **Windows** |
| Function keys | n/a | Handles media rows behind **Fn** |
| Copilot key | n/a | Works, via a key remap |
| Overlay | — | 340×48 pill, ~1% of screen, never takes focus |
| Engines | Cohere/Parakeet/Whisper + more | Whisper (local) |
| Language | Rust | Python |

**Be straight about the trade-offs.** Voxtype is faster (9–11× realtime on CPU vs
our ~2–3s) and has more engine choice. Don't pretend otherwise — someone will
benchmark it, and honesty costs nothing you can't afford to lose.

**Who it's for:** Windows users who want offline dictation, and anyone coming
from Voxtype/BoxType on Linux who now needs the same thing on Windows.

---

## 2. Assets already live (no work needed)

- Repo description rewritten to lead with outcome, not the fork
- 12 topics set: `voice-typing`, `dictation`, `whisper`, `speech-to-text`,
  `windows`, `windows-11`, `productivity`, `offline-first`, `accessibility`, etc.
  These are how GitHub search and the Windows-clicker crowd actually find things.
- README opens with the outcome, a config snippet, and the three differentiators
- Screenshots: Settings, scrolled Settings, and the indicator pill

---

## 3. Show HN — draft

> **Title:** Show HN: ghosttype – push-to-talk dictation for Windows that stays out of your way
>
> **URL:** https://github.com/gdeyoung/ghosttype

I built this because dictation on Windows kept hitting the same walls: Win+H
wants the cloud and gets confused by proper nouns, and every open-source
alternative I tried either grabbed focus (so the text landed in the app's own
overlay) or covered a third of the screen.

ghosttype runs Whisper locally — no API key, no account, nothing leaving the
machine — and the only UI is a 340×48 pill while you speak, about 1% of the
screen. It never takes focus, so the text goes to the app you were typing in.

Two hardware problems it handles that most builds ignore:
- **Media function rows.** On most modern laptops F1–F12 sit behind the Fn key,
  so a "just press F9" hotkey needs two hands. ghosttype defaults to F13+.
- **The Copilot key.** Windows eats that key before any app can see it — a pynput
  probe on my machine recorded zero events. ghosttype documents the
  `SendInput` remap that works around it.

It's a fork of CatBoneheaD/Whisper-Writer, which is a fork of
savbell/whisper-writer. Credit to both — I fixed a crash, completed a
half-finished UI translation, and rebuilt the indicator.

Windows-only right now. The Linux equivalent people ask about is Voxtype, which
is better and faster; this is the Windows gap.

---

## 4. Reddit — drafts

Pick the one subreddit that actually fits. Cross-posting the same text to
r/Windows11, r/commandline, and r/productivity reads as spam and gets buried.

**r/Windows11**
> Built a Windows dictation app because Win+H kept mishearing me and the
> open-source options all grabbed keyboard focus.
>
> ghosttype runs Whisper locally (no API key, nothing leaves the machine). Press
> a hotkey, speak, text lands in whatever app you're using. The only UI is a
> small pill that shows it's listening — it deliberately never takes focus, which
> is the thing most of these apps get wrong.
>
> Handles the two things that broke every other build on my laptop: function keys
> that need Fn held, and the Copilot key Windows won't let apps bind.
>
> https://github.com/gdeyoung/ghosttype
>
> Feedback welcome, especially from anyone with a different keyboard.

**r/commandline**
> Windows equivalent of Voxtype, roughly. Push-to-talk dictation with a local
> Whisper model — no API key, no telemetry.
>
> Two hardware details that took the most work: laptops with media function rows
> (F1–F12 behind Fn, so a single-key hotkey has to be F13+), and the Copilot key,
> which Windows consumes before any app sees it.
>
> Python/PyQt5 if you want to hack on it: https://github.com/gdeyoung/ghosttype

**r/productivity** — lead with the workflow, not the tech:
> If you dictate more than you type: I made a Windows dictation app that stays
> out of your way.
>
> It sits in the tray, shows a small pill only while you're talking, and never
> takes keyboard focus — so the text lands in the app you were already using.
> Runs entirely offline on a local Whisper model.
>
> https://github.com/gdeyoung/ghosttype

---

## 5. Where else it's worth showing up

**High value, low effort:**

- **Hacker News** — the Show HN above. Post weekday morning US time.
- **GitHub topics** — done. Topic discovery is how a lot of Windows tooling gets
  found; expect trickle traffic for weeks, not a spike.
- **Your own blog / a `ghosttype` GitHub Pages site** — a real landing page with
  the GIF, install steps, and the Voxtype comparison. Highest leverage long-term
  because it's the one URL you can put anywhere without asking permission.
- **Windows-focused communities** — r/PowerShell, Windows dev Discords, the
  "Software Recommendations" threads people already browse.

**Worth a demo GIF.** The single highest-value asset. 10–15 seconds: hold the
hotkey, the pill appears, speak, text lands in Notepad, pill flashes "Typed".
`make_screenshots.py` already renders the UI offscreen; a scripted GIF of the
real flow would be straightforward. Say the word.

**Skip:** Product Hunt (it's a saturated launchpad for a free GitHub tool),
and any "best Windows apps" listicle (they're all paid placements).

---

## 6. Honest expectations

This is a public repo, one day old, 0 stars, no CI, and a single maintainer.
Realistic outcomes:

- **Show HN:** a few upvotes and one or two comments, occasionally a front page
  if the timing is lucky. Most Show HNs die quietly.
- **Reddit:** one good thread in the right subreddit is worth more than a
  front page that bounces.
- **Topics:** slow, compounding discovery over months.

The realistic outcome is a handful of stars and a few users who tell you it
works. That's fine — it's a tool you wanted, and the diff against upstream is
genuinely useful to anyone on a Windows laptop.

**One thing that would help more than any launch:** a CI badge and one honest
screenshot in the PR description. Right now "does this even run on Windows CI?"
is unanswered, and that's the first question any technical reviewer will ask.
