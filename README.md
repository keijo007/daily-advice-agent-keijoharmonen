# Personal Signal OS

Practical daily intelligence brief system.

The project collects selected sources, filters noise, scores useful signals, and writes one daily markdown brief.

## What It Produces

Output file:
- `outputs/daily_briefs/YYYY-MM-DD.md`

Daily brief sections:
1. Top Signals
2. Opportunities
3. Claims to Verify
4. Weak Signals
5. Thinking Mirror
6. Recommended Action Today
7. Ignore / Low Priority

## Architecture

1. Source collectors
2. Normalization
3. Storage
4. Signal scoring
5. Agent-style analysis modules
6. Daily brief generation
7. Feedback capture

## Source Support (MVP)

Working now:
- RSS feeds from `config/sources.yaml`
- Local files:
  - `data/personal/goals.md`
  - `data/personal/current_state.yaml`
  - `data/personal/diary/*.md`

Prepared stubs (no credentials required yet):
- Gmail
- Outlook
- Telegram
- Calendar
- YouTube

## Configuration

Copy and edit examples:
- `config/sources.example.yaml` -> `config/sources.yaml`
- `config/settings.example.yaml` -> `config/settings.yaml`

Required personal files:
- `data/personal/goals.md`
- `data/personal/current_state.yaml`
- `data/personal/diary/`

## Run Commands

Preferred (requested):
- `python -m src.main collect`
- `python -m src.main score`
- `python -m src.main brief`
- `python -m src.main run-daily`
- `python -m src.main feedback --item-id <id> --rating + --note "optional"`

Equivalent app entry:
- `python -m app.signal_os_main run-daily`

## Storage

SQLite:
- `data/insights.db`

JSONL exports:
- `data/raw_items.jsonl`
- `data/normalized_items.jsonl`
- `data/scored_items.jsonl`
- `data/feedback.jsonl`

Markdown output:
- `outputs/daily_briefs/`

## Scoring Model

Transparent weighted score:

`signal_score = 2.0*relevance + 1.5*actionability + 1.5*deadline_urgency + 1.2*novelty + 1.0*source_quality + 1.0*repeated_across_sources + 0.8*personal_fit - 1.5*distraction_risk - 1.0*weak_evidence`

Classification:
- SIGNAL
- WEAK_SIGNAL
- OPPORTUNITY
- VERIFY
- NOISE

## Privacy Notes

- Diary/current_state are processed locally by default.
- Diary is not sent to external LLM unless `privacy.allow_external_llm_for_diary: true`.
- No credentials are hardcoded; use environment variables.

## Feedback

Store signal quality feedback in `data/feedback.jsonl`:
- `+` useful
- `-` useless
- `?` maybe later
- `!` very important

Future scoring updates can use this feedback to tune weights and source/topic relevance.

## Current Limitations

- Repetition detection is heuristic (title/url/source overlap).
- Claim verification is guidance-level (no automated fact-check browsing yet).
- Stub integrations are placeholders until official API setup is added.
