# Personal Signal OS

## One such text about yourself can be better during a break than reading LinkedIn, X, Telegram etc. post. You only have to set your goals, then open the app (for exmpl. Notes) and read your advice.

## The agent reads the same information you do: your diary, (WhatsApp)(not yet), Telegram, YouTube transcriptions, news and more. Every day, it combines your goals with your real-time information and give you signal filtered summary and advice(for example it can detect your thinking biases and help better uderstand yourself). Sometimes, that can be exactly what you need. 

# What It Produces

Output file (in my OneDrive):
outputs/daily_briefs/YYYY-MM-DD.md

Daily brief sections:
1. Top Signals
2. Opportunities
3. Claims to Verify
4. Weak Signals
5. Thinking Mirror
6. Recommended Action Today
7. Ignore / Low Priority

# Architecture

1. Source collectors
2. Normalization
3. Storage
4. Signal scoring
5. Agent-style analysis modules
6. Daily brief generation
7. Feedback capture

### Agent Architecture

Signal Summary agent takes the highest-scoring items and turns them into short signal cards, including why each signal matters and what action it suggests.

Opportunity agent sorts and prioritizes extracted opportunities, mainly by urgency and deadline.
A Claim Checker agent ranks claims that should be verified, especially those that are important, data-backed, or tied to deadlines and opportunities.

Reflection agent generates a “Thinking Mirror”, which is a lightweight personal reflection layer. It tries to identify your repeated focus, a possible blind spot, a possible bias, and one question worth asking yourself. If diary privacy settings allow it, this can use an LLM; otherwise it falls back to heuristics.

Brief Synthesizer combines all of that into the final daily brief and decides the single recommended action for today.

# PIPELINE

1. Collectors read from local notes, diaries, exports, RSS feeds, and optional connected servicces.
2. Normalisation converts every input into a shared internal item format.
3. Deduplication removes repeated or overlapping content.
4. Storage preserves raw, normalized, and scored data for traceability.
5. Signal scoring ranks items by relevance, actionability, urgency, novelty, and personal fit.
6. Analysis agents turn ranked items into interpretation, reflection, and advice.
7. The brief renderer writes one markdown brief for the day.
8. Feedback can later improve ranking and filtering behavior.

### Sources

- ONEDRIVE files:
`data/personal/goals.md`
`data/personal/current_state.yaml`
`data/personal/diary/*.md`

OTHER:
- RSS
- Gmail
- Outlook
- Telegram
- Calendar (not yet)
- YouTube (not yoe)

### Why This Project Exists (For Building AI cource)

Most information tools tell you what happened somewhere. This one is designed to tell you what matters for you today.

- It combines goals, diary context, and selected feeds into one readable daily output.
- It filters noise instead of rewarding more scrolling.
- It separates promising opportunities from weak evidence.
- It flags claims that should be verified before you act on them.
- It mirrors your own patterns, not only the outside world.

The output is meant to feel closer to a personal operating system than a generic news digest.

### What The Daily Brief should Contains (But so unstable) and scoring

Each generated brief is structured for short, high-value reading during a break.

- Top Signals: the strongest items worth attention right now.
- Opportunities: ideas, openings, or leverage points with upside.
- Claims to Verify: useful-looking items that still need validation.
- Weak Signals: early hints that may matter later.
- Thinking Mirror: patterns, biases, or goal misalignment found in your own material.
- Recommended Action Today: one practical step for the current day.
- Ignore / Low Priority: items that should not consume attention now.

SCORING below:

`signal_score = 2.0*relevance + 1.5*actionability + 1.5*deadline_urgency + 1.2*novelty + 1.0*source_quality + 1.0*repeated_across_sources + 0.8*personal_fit - 1.5*distraction_risk - 1.0*weak_evidence`

Current output classes:
- `SIGNAL`
- `WEAK_SIGNAL`
- `OPPORTUNITY`
- `VERIFY`
- `NOISE`

### Privacy And Control

- Diary and current-state material are processed locally by default.
- Diary content is not sent to an external LLM unless `privacy.allow_external_llm_for_diary: true`.
- Credentials are not hardcoded into the repository.
- The system can remain fully local if you only use file-based inputs.

