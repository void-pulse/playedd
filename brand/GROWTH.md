# Playedd — Subscriber-conversion plays (added 2026-06-10)

The Shorts bring swipe traffic; these plays convert swipers into subscribers. The lane + publish tasks apply them.

## The tribe: "the Stans"
Subscribers are **the Stans** (Stan the mascot + "stan" = superfan — double meaning, ties the character to the community). CTA = **"Become a Stan."** Use it in:
- the standalone daily-short CTA end card heading: `--cta-heading "BECOME A,STAN"` (replaces "FOLLOW FOR DAILY WONDER" for standalone wonder shorts; episode teasers keep "FOR FULL,BREAKDOWN" since they drive to the full video).
- pinned comments + descriptions ("Become a Stan — one of these every day").
(Soft-launched; if it doesn't land we fall back to "Wonderers" — names are reversible.)

## The streak: "DAILY WONDER #N"
Stamp a climbing counter on every standalone wonder short's CTA card via `build_short.py --badge "DAILY WONDER #N"`. N = cumulative count of standalone wonder shorts made (count dirs under `shorts_daily/*/`, excluding manifests, + this short's position). A visible, climbing number = FOMO ("don't miss the next") + credibility ("they've made 300+ of these"). The daily habit is the sub pitch.

## The comment-fueled loop (highest-ROI converter)
Standard pinned comment on wonder shorts does double duty — sub CTA + topic engine:
> `Become a Stan 👇 one mind-bender every day. Drop a "wait, that's true?" fact below — I might make it into a short.`
People subscribe to see if theirs gets picked; comments surge (algorithm loves it); you get an endless topic pipeline. When a commenter's fact becomes a short, credit them on screen.

## Daily-series framing
Lean every short's close + CTA into the daily promise: "Follow / become a Stan — a new mind-bender every day." The cadence IS the pitch.

## Occasional format: cliffhanger 2-parters
Some shorts: pose the wild question, stop on "…the answer's stranger than you think — part 2 tomorrow." Subscribing becomes the way to get the payoff. Use sparingly (don't bait-and-switch every time).

## Milestone / "Wall of Wonderers" (future, episodic + manual)
Once there's an engaged comment base: feature subscriber comments/questions inside episodes (a recurring segment). Subscribing + commenting becomes a never-expiring lottery ticket. Keep wording to "featuring fans," never "sub to win" (YouTube ToS).

## The shorts ↔ episodes loop
Two lanes that feed each other. Most daily shorts are standalone ("Become a Stan" card + streak). But when a short's topic maps to an existing/queued EPISODE, it becomes a **teaser**: "FOR FULL BREAKDOWN" card, no streak badge, related-video link + episode-linking pinned comment set at publish. Shorts = the wide top-of-funnel hook; episodes = the depth that earns the subscribe and the watch-time. The lane routes the CTA automatically (see playedd-daily-wonder-shorts-lane). Channel positioning reflects both: "Daily mind-benders. Weekly deep dives." (see brand/CHANNEL_PAGE.md).

## Honest priority
The **comment-loop + daily-series streak** convert the traffic we already get and compound. The milestone gimmick is a one-time spike on top. Watch Studio analytics: if per-short views hold as volume rises, push higher; if they drop, that's the ceiling.
