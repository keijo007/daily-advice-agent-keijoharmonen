# Personal Signal OS

### One such text about yourself can be better during a break than reading LinkedIn, X, Telegram etc. post. You only have to set your goals, then open the app (for exmpl. Notes) and read your advice.
### The agent reads the same information you do: your diary, (WhatsApp)(not yet), Telegram, YouTube transcriptions, news and more. Every day, it combines your goals with your real-time information and give you signal filtered summary and advice(for example it can detect your thinking biases and help better uderstand yourself). Sometimes, that can be exactly what you need. 
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

## External Credentials (Still Supported)

The current codebase still supports external integrations when you want to expand beyond local files. You can start with a fully local setup, then enable connected collectors one by one.

Environment variables still used by the program:

- `OPENAI_API_KEY` for optional LLM summaries and coaching output.
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `ONEDRIVE_REFRESH_TOKEN` for Microsoft Graph and OneDrive flows, including Outlook, exports, and uploads.
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` for the Gmail collector.
- `OUTLOOK_CLIENT_ID`, `OUTLOOK_CLIENT_SECRET`, `OUTLOOK_REFRESH_TOKEN` for the Outlook collector.
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING` for the Telegram collector.
- `TOKEN_GITHUB` reserved for a future GitHub collector.

To enable Gmail, Outlook, Telegram, or YouTube collection, turn on the related `email.enabled` or `social.enabled` flags in `config/sources.yaml`, or use the matching switches in `config/settings.yaml`.

## Why This Project Exists

Most information tools tell you what happened somewhere. This one is designed to tell you what matters for you today.

- It combines goals, diary context, and selected feeds into one readable daily output.
- It filters noise instead of rewarding more scrolling.
- It separates promising opportunities from weak evidence.
- It flags claims that should be verified before you act on them.
- It mirrors your own patterns, not only the outside world.

The output is meant to feel closer to a personal operating system than a generic news digest.

## How It Works

The pipeline is intentionally transparent and easy to inspect.

1. Collectors read from local notes, diaries, exports, RSS feeds, and optional connected services.
2. Normalization converts every input into a shared internal item format.
3. Deduplication removes repeated or overlapping content.
4. Storage preserves raw, normalized, and scored data for traceability.
5. Signal scoring ranks items by relevance, actionability, urgency, novelty, and personal fit.
6. Analysis agents turn ranked items into interpretation, reflection, and advice.
7. The brief renderer writes one markdown brief for the day.
8. Feedback can later improve ranking and filtering behavior.

## Agent Architecture

The system uses specialized agents instead of a single general-purpose assistant.

- Reader agent summarizes external material and preserves key topics, quotes, and factual distinctions.
- Reflection agent examines goals and recent diary entries to detect patterns, blind spots, and possible thinking biases.
- Coach agent combines the outside view and the inside view into one practical recommendation for today.

This separation keeps the reasoning more testable and reduces the risk of mixing raw observation with advice too early.

## What The Daily Brief Contains

Each generated brief is structured for short, high-value reading during a break.

- Top Signals: the strongest items worth attention right now.
- Opportunities: ideas, openings, or leverage points with upside.
- Claims to Verify: useful-looking items that still need validation.
- Weak Signals: early hints that may matter later.
- Thinking Mirror: patterns, biases, or goal misalignment found in your own material.
- Recommended Action Today: one practical step for the current day.
- Ignore / Low Priority: items that should not consume attention now.

Output location:

- `outputs/daily_briefs/YYYY-MM-DD.md`

## Configuration

The easiest setup path is local-first.

1. Copy `config/sources.example.yaml` to `config/sources.yaml`.
2. Copy `config/settings.example.yaml` to `config/settings.yaml`.
3. Create or fill the core personal files:
   - `data/personal/goals.md`
   - `data/personal/current_state.yaml`
   - `data/personal/diary/`
4. Add external credentials only for the collectors you actually want to use.

This keeps the project usable from day one, even without API setup.

## Run Commands

Main workflow:

- `python -m src.main collect`
- `python -m src.main score`
- `python -m src.main brief`
- `python -m src.main run-daily`
- `python -m src.main feedback --item-id <id> --rating + --note "optional"`

Alternative app entry:

- `python -m app.signal_os_main run-daily`

## Data And Outputs

Persistent storage and generated artifacts:

- SQLite database: `data/insights.db`
- Raw export: `data/raw_items.jsonl`
- Normalized export: `data/normalized_items.jsonl`
- Scored export: `data/scored_items.jsonl`
- Feedback log: `data/feedback.jsonl`
- Rendered briefs: `outputs/daily_briefs/`

This layout makes every stage inspectable, from incoming content to final recommendation.

## Signal Scoring

Signal ranking is intentionally transparent rather than hidden behind a black box.

`signal_score = 2.0*relevance + 1.5*actionability + 1.5*deadline_urgency + 1.2*novelty + 1.0*source_quality + 1.0*repeated_across_sources + 0.8*personal_fit - 1.5*distraction_risk - 1.0*weak_evidence`

Current output classes:

- `SIGNAL`
- `WEAK_SIGNAL`
- `OPPORTUNITY`
- `VERIFY`
- `NOISE`

## Privacy And Control

- Diary and current-state material are processed locally by default.
- Diary content is not sent to an external LLM unless `privacy.allow_external_llm_for_diary: true`.
- Credentials are not hardcoded into the repository.
- The system can remain fully local if you only use file-based inputs.

## Feedback

The project includes a lightweight feedback loop in `data/feedback.jsonl`:

- `+` useful
- `-` useless
- `?` maybe later
- `!` very important

That signal can later be used to tune ranking weights, source trust, and personal relevance.

## Current Limitations

- Repetition detection is still heuristic and relies on overlaps such as title, URL, and source identity.
- Claim verification is advisory rather than a full automated fact-checking workflow.
- Some collectors are prepared integration surfaces and still need full API or credential setup before they are production-ready.
