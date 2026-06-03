# Daily Insight Agent - GitHub Actions Edition

🤖 **Automated daily insights using AI agents + GitHub Actions + GitHub Pages**

Generates a daily summary page from your goals, diary entries, and other configured sources.

This repo is built for GitHub Pages publishing and optional OneDrive upload.

---

## 📁 Current project structure

```
.github/workflows/
  daily-insight.yml         ← Scheduled pipeline run
scripts/
  generate_insight.py       ← Main generator
  generate_insight_safe.py  ← Safer local workflow helper
  upload_to_onedrive.py     ← Optional direct upload tool
app/                        ← Core pipeline, agents, collectors
data/                       ← Local source files (diary, goals, exports)
index.html                  ← Published GitHub Pages page
```

---

## ⚙️ How it works

Daily run flow:

1. GitHub Actions triggers `scripts/generate_insight.py`
2. `DailyPipeline` collects diary/goals/feeds
3. Reader, Reflection, and Coach agents analyze the data
4. `index.html` is generated
5. The repository is updated and GitHub Pages publishes the page

> Local `data/daily_insights` storage is no longer used for daily output.

---

## 🔧 Configuration

### OneDrive upload (optional)

This repo can optionally write daily insight output to OneDrive.

Required environment variables:

- `OPENAI_API_KEY`
- `UPLOAD_DAILY_INSIGHTS_TO_ONEDRIVE=true`

OneDrive upload targets:

- `ONEDRIVE_DAILY_INSIGHTS_PATH`
- `ONEDRIVE_DAILY_INSIGHTS_SHARE_URL`

If explained by your setup, provide Azure credentials too:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

---

## 📚 Setup

### 1. Configure GitHub Secrets

Go to your repository settings and add:

- `OPENAI_API_KEY`
- Optional OneDrive secrets if you want cloud upload

### 2. Run locally

```bash
python scripts/generate_insight.py
```

or for a safer helper:

```bash
python scripts/generate_insight_safe.py
```

### 3. GitHub Pages

Configure Pages:

- Branch: `main`
- Folder: `/`

Published URL:

- `https://yourusername.github.io/daily-insights/`

---

## 💾 Storage and publishing

This project generates `index.html` as the main published output.

- `index.html` is the GitHub Pages artifact
- OneDrive upload is optional and controlled by env vars
- No local daily insight JSON file is required for normal operation

---

## 🐛 Troubleshooting

### Workflow fails

1. Open Actions logs
2. Confirm `OPENAI_API_KEY` is set correctly
3. Run locally with `python scripts/generate_insight.py`

### OpenAI key issue

- Secret name must be exactly `OPENAI_API_KEY`
- No leading or trailing spaces

### GitHub Pages not updating

- Check Pages settings
- Wait 1-2 minutes after push

---

## 💰 Cost estimate

| Component | Cost |
|-----------|------|
| GitHub Actions | Free within runner limits |
| GitHub Pages | Free |
| OpenAI API | Small monthly cost depending on usage |
| Domain | Optional (€5-10/year) |

---

## 📖 Documentation

- [`.github/README.md`](.github/README.md) - GitHub Actions guide
- [`BUDGET_DEPLOYMENT.md`](BUDGET_DEPLOYMENT.md) - Deployment notes
- [`GITHUB_ACTIONS_SAFE_SETUP.md`](GITHUB_ACTIONS_SAFE_SETUP.md) - Safe setup guide
- [`GITHUB_ACTIONS_SUMMARY.md`](GITHUB_ACTIONS_SUMMARY.md) - Workflow summary
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - System architecture

---

## ✅ Checklist

- [ ] `OPENAI_API_KEY` set
- [ ] Workflow tested
- [ ] GitHub Pages configured
- [ ] OneDrive upload configured if desired

---

## 🎉 Ready

The system publishes a daily AI-generated insight page automatically.

---

## Notes for developers

This repo is built around:

- `app/services/daily_pipeline.py`
- `app/agents/reader_agent.py`
- `app/agents/reflection_agent.py`
- `app/agents/coach_agent.py`

Use the `scripts/upload_to_onedrive.py` tool only if you want a direct OneDrive backup.


This README explains:
- ✅ What data goes in and where
- ✅ Where it's stored and how
- ✅ Where OpenAI API is called
- ✅ How the daily tip is generated
- ✅ How the phone shortcut works
- ✅ What to do next to make it work

Happy building! 🚀
