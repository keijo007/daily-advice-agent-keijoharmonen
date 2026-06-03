# Daily Insight Agent - GitHub Actions Edition

🤖 **Automated daily insights using AI agents + GitHub Actions + GitHub Pages**

Generates personalized daily summaries based on your goals, diary, and interests. Deployed completely free using GitHub's free tier.

**Budjetti**: €5-10/vuosi (vain domain)

---

## 📁 Tiedostorakenne

```
.github/workflows/
  daily-insight.yml         ← Automaattinen päivittäinen ajo
scripts/
  generate_insight.py       ← Pääskripti
data/
index.html                  ← GitHub Pages näyttää tätä
```

---

## ⚙️ Miten toimii

Päivittäin 06:00 UTC
        ↓
 GitHub Actions
        ↓
scripts/generate_insight.py
        ↓
 DailyPipeline
        ↓
Reader + Reflection + Coach Agents (OpenAI)
        ↓
 HTML page update
        ↓
git commit & push
        ↓
GitHub Pages update
        ↓
https://daily-insights.com ✓
```

---

## 🔧 Konfigurointi

### Muuta ajastusta

`.github/workflows/daily-insight.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # ← Muuta tätä
```

Cron-muoto: `minute hour day month day-of-week`
- `0 6 * * *` = 06:00 UTC joka päivä
- `0 9 * * 1-5` = 09:00 UTC maanantaista perjantaihin
- Helppo: https://crontab.guru

---

## 📚 Asennus

### 1. GitHub Secrets

`https://github.com/yourusername/daily-insights/settings/secrets/actions`

**Pakollinen:**
- `OPENAI_API_KEY` = `sk-proj-...`

**Valinnainen (OneDrive):**
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

### 2. Testaa

```
Repository → Actions → Daily Insight Generator → Run workflow
```

### 3. GitHub Pages

```
Settings → Pages
- Branch: main
- Folder: /
```

URL: `https://yourusername.github.io/daily-insights/`

### 4. Domain (valinnainen)

Hanki domain: GoDaddy/Namecheap (~€5-10/vuosi)

Konfiguroi DNS:
```
CNAME: daily-insights.com → yourusername.github.io
```

GitHub:
```
Settings → Pages → Custom domain → daily-insights.com
```

---

## 💾 Tallennus ja julkaisu

Tämä projekti tuottaa HTML-sivun `index.html`, joka on GitHub Pages -julkaisun lähde.

### GitHub Pages

- `index.html` päivitetään automaattisesti
- Näkyy GitHub Pages -sivuna

### OneDriveen (valinnainen)

Jos OneDrive on konfiguroitu, insight voidaan ladata myös suoraan pilveen.

- `ONEDRIVE_DAILY_INSIGHTS_PATH` tai `ONEDRIVE_DAILY_INSIGHTS_SHARE_URL`
- `UPLOAD_DAILY_INSIGHTS_TO_ONEDRIVE=true`

> Paikallista `data/daily_insights`-kansiota ei enää käytetä insightien tallennukseen.

---

## 🐛 Vikadiagnosa

### Workflow epäonnistuu?

1. Katso lokit:
   ```
   Repository → Actions → Daily Insight Generator → [viimeisin run] → Logs
   ```

2. Tarkista Secrets:
   ```
   Settings → Secrets and variables → Actions
   - OPENAI_API_KEY asetettu?
   - Oikealla arvolla (ei välilyöntejä)?
   ```

3. Testaa paikallisesti:
   ```bash
   python scripts/generate_insight.py
   ```

### "OpenAI API key not found"?

- Settings → Secrets → OPENAI_API_KEY
- Tarkista että nimi on TASAN: `OPENAI_API_KEY`
- Ei välilyöntejä alussa/lopussa

### GitHub Pages ei näy?

```
Settings → Pages
- Branch: main
- Folder: /
- Odota 1-2 minuuttia
```

---

## 💰 Kustannukset

| Komponentti | Hinta |
|-------------|-------|
| GitHub Actions | €0 (2000 min/kk) |
| GitHub Pages | €0 |
| OpenAI API | €0.47/vuosi |
| Domain (valinnainen) | €5-10/vuosi |
| **YHTEENSÄ** | **€5-10/vuosi** |

---

## 📖 Dokumentaatio

- [`.github/README.md`](.github/README.md) - GitHub Actions ohjeet
- [`BUDGET_DEPLOYMENT.md`](BUDGET_DEPLOYMENT.md) - Yksityiskohtainen opas
- **[`GITHUB_ACTIONS_SAFE_SETUP.md`](GITHUB_ACTIONS_SAFE_SETUP.md) - TURVALLINEN SETUP!**
- **[`GITHUB_ACTIONS_SUMMARY.md`](GITHUB_ACTIONS_SUMMARY.md) - Yhteenveto**
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Tekninen rakenne (AI & kehittäjille)

---

## ✅ Tarkistuslista

- [ ] OpenAI API-avain hankittu
- [ ] GitHub Secrets asetettu
- [ ] Workflow testattu (Run workflow)
- [ ] Tulokset näkyvät (Actions → Logs)
- [ ] GitHub Pages konfiguroitu
- [ ] Domain ostettu (valinnainen)

---

## 🎉 Valmis!

Sovellus pyörii nyt **24/7** ilman paikallista konetta.

Päivittäinen yhteenveto näkyy:
- `https://yourusername.github.io/daily-insights/`
- Tai omalla domainillasi: `https://daily-insights.com`

Generointi tapahtuu **automaattisesti klo 06:00 UTC** jika päivä.

---

## 🤖 AI-analyysia varten

Haluat AI:n analysoivan tai kehittävän järjestelmää?

**Kopioi nämä tiedostot AI:lle:**

1. **README.md** (tämä) - Käytönotto
2. **ARCHITECTURE.md** - Tekninen rakenne
3. **AGENTS.md** - Agentit-järjestelmä
4. Kaikki tiedostot `app/`-kansiosta

**Komennolla:**
```bash
cat README.md ARCHITECTURE.md AGENTS.md > ai_context.txt
# Kopioi sisältö AI:lle
```

AI ymmärtää nyt:
- ✅ Kolmen agentin filosofia
- ✅ Data flow (keruu → analyysi)
- ✅ Komponentin arkkitehtuuri
- ✅ Laajentamispisteet
- ✅ Koodi-organisaatio

AI voi kehittää:
- ✅ Uusia agentteja
- ✅ Uusia keräilijöitä
- ✅ Parannuksia promteihin
- ✅ Uusia ominaisuuksia
✅ **Privacy by Design** - Limited data sent to external APIs
✅ **Error Resilience** - If one source fails, others continue
✅ **Lazy Evaluation** - Generate insight only when needed
✅ **Agent Orchestration** - Agents work in sequence with clear inputs/outputs

---

## Resources

- OpenAI API: https://platform.openai.com/docs
- FastAPI: https://fastapi.tiangolo.com
- SQLite: https://www.sqlite.org/docs.html
- Agent Design: https://en.wikipedia.org/wiki/Intelligent_agent
- Python async: https://realpython.com/async-io-python/

---

## Questions?

This README explains:
- ✅ What data goes in and where
- ✅ Where it's stored and how
- ✅ Where OpenAI API is called
- ✅ How the daily tip is generated
- ✅ How the phone shortcut works
- ✅ What to do next to make it work

Happy building! 🚀
