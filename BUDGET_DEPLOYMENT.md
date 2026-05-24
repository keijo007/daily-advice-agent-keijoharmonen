# 💰 Super-halpa pilvipalvelu - €10/vuosi budjetti

## 🎯 Tavoite
Sovellus pyörii **ilmaisesti** tai alle €10/vuosi:
- ✅ Linkki jolla pääsee (`https://daily-insights.com`)
- ✅ Päivittäinen analyysit generoidaan automaattisesti
- ✅ Data tallentuu OneDriveen ja/tai GitHub-repoon
- ✅ Kone voi olla sammutettuna 24/7
- ✅ Budjetti: 0€ + domain €5-10 = **alle €10/vuosi**

---

## 💡 Ratkaisu: GitHub Actions + GitHub Pages (Ilmainen!)

### Miten se toimii

1. **GitHub Actions ajaa koodin päivittäin** (ilmainen, 2000 min/kk)
   - Generoi päivittäisen insight
   - Tallentaa HTML-tiedoston GitHub-repoon
   
2. **GitHub Pages hostaa tulokset** (ilmainen)
   - Näytetään osoitteessa `https://daily-insights.com`
   
3. **Data tallentuu**:
   - OneDriveen (pilvi-backup)
   - GitHub-repoon (versionhallinta)
   
4. **Kustannus**: Vain domain (~€5-10/vuosi)

---

## 🚀 Asennusohje (5 minuutissa)

### 1️⃣ GitHub-tili ja repository

```bash
# Paikallisesti
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/daily-insights.git
git branch -M main
git push -u origin main
```

### 2️⃣ GitHub Secrets asetus (API-avaimet)

Mene: `https://github.com/yourusername/daily-insights/settings/secrets/actions`

Lisää nämä:
- `OPENAI_API_KEY` = sk-proj-...
- `AZURE_CLIENT_ID` = (valinnainen, jos OneDrive)
- `AZURE_CLIENT_SECRET` = (valinnainen)
- `AZURE_TENANT_ID` = (valinnainen)

### 3️⃣ Luodaan GitHub Actions workflow

Luo tiedosto `.github/workflows/daily-insight.yml`:

```yaml
name: Daily Insight Generator

on:
  schedule:
    # Suoritetaan joka päivä 06:00 UTC (klo 8 Suomessa kesällä)
    - cron: '0 6 * * *'
  
  # Voit myös ajaa manuaalisesti
  workflow_dispatch:

jobs:
  generate-insight:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests
      
      - name: Generate daily insight
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
        run: |
          python scripts/generate_insight.py
      
      - name: Commit and push results
        run: |
          git config user.email "action@github.com"
          git config user.name "Daily Insight Bot"
          git add data/daily_insights/*
          git commit -m "Daily insight $(date +%Y-%m-%d)" || true
          git push
```

### 4️⃣ Luodaan script joka generoi HTML-sivun

Luo `scripts/generate_insight.py`:

```python
"""Generate daily insight and create HTML page."""

import json
from datetime import datetime
from pathlib import Path
from app.services.daily_pipeline import DailyPipeline

def generate_html(insight):
    """Create beautiful HTML page from insight."""
    html = f"""
    <!DOCTYPE html>
    <html lang="fi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Insight - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
                line-height: 1.6;
            }}
            .container {{
                background: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #3498db; margin-top: 30px; }}
            .date {{ color: #7f8c8d; font-size: 14px; }}
            .tip {{ 
                background: #e8f4f8;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .warning {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Päivittäinen yhteenveto</h1>
            <p class="date">{datetime.now().strftime('%d.%m.%Y')}</p>
            
            <h2>📰 Tänään lukemasi</h2>
            <p>{insight.get('reader_summary', 'Ei sisältöä')}</p>
            
            <h2>🧠 Havainnot ajattelustasi</h2>
            <p>{insight.get('reflection_summary', 'Ei analyyseja')}</p>
            
            <h2>💡 Tämän päivän vinkki</h2>
            <div class="tip">
                {insight.get('practical_tip', 'Ei vinkkejä')}
            </div>
            
            <h2>🎯 Toimintaohje</h2>
            <p>{insight.get('one_day_action', 'Ei toimintaa')}</p>
            
            <h2>⚠️ Huomioitavaa</h2>
            <div class="warning">
                {insight.get('warnings', 'Ei varoituksia')}
            </div>
        </div>
    </body>
    </html>
    """
    return html

def main():
    """Generate insight and save as HTML."""
    print("🚀 Generating daily insight...")
    
    try:
        # Run pipeline
        pipeline = DailyPipeline()
        insight = pipeline.run()
        
        if insight:
            # Create output directory
            output_dir = Path("data/daily_insights")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as HTML
            today = datetime.now().strftime("%Y-%m-%d")
            html_file = output_dir / f"{today}.html"
            
            html_content = generate_html(insight)
            html_file.write_text(html_content, encoding="utf-8")
            
            # Also save as JSON
            json_file = output_dir / f"{today}.json"
            json_file.write_text(
                json.dumps(insight, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            # Create index.html (latest insight)
            index_file = output_dir.parent / "index.html"
            index_file.write_text(html_content, encoding="utf-8")
            
            print(f"✓ Insight saved to {html_file}")
            print(f"✓ Index updated")
            
        else:
            print("✗ Failed to generate insight")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

if __name__ == "__main__":
    main()
```

### 5️⃣ GitHub Pages käyttöönotto

1. Repository-asetuksissa (`Settings`):
   - GitHub Pages → Source: Deploy from branch
   - Branch: main
   - Folder: `/` (tai `/docs`)

2. URL on nyt: `https://yourusername.github.io/daily-insights`

### 6️⃣ Oman domainin liittäminen (€5-10/vuosi)

**Hanki domain** (esim. GoDaddy, Namecheap):
- `daily-insights.com` ≈ €5-10/vuosi

**Konfiguroi DNS**:
- GoDaddyssa (tai muualla):
  - CNAME: `daily-insights.com` → `yourusername.github.io`
  
- GitHub:
  - Settings → Pages → Custom domain
  - Anna `daily-insights.com`

Nyt: `https://daily-insights.com` toimii! 🎉

---

## 📊 Arkkitehtuuri

```
Päivittäin 06:00 UTC
        ↓
GitHub Actions
        ↓
  Python script
        ↓
    Pipeline
        ↓
  - Reader Agent (OpenAI API)
  - Reflection Agent (OpenAI API)
  - Coach Agent (OpenAI API)
        ↓
    HTML-sivu + JSON
        ↓
  Commit to GitHub
        ↓
GitHub Pages updates
        ↓
https://daily-insights.com ← Näytetään pagesilla
```

---

## 💾 Data-tallentaminen

### Vaihtoehto 1: GitHub-repoon (Git versiointi)

Kaikki JSON/HTML tallentuu repoon:
```
data/daily_insights/
  ├── 2026-05-21.json
  ├── 2026-05-21.html
  ├── 2026-05-22.json
  └── 2026-05-22.html
```

✅ Etu: Versionhallinta, helppo selata
✅ Etu: Ilmainen backup (GitHub)
❌ Haitta: GitHub rajoittaa repon kokoa (100 MB)

### Vaihtoehto 2: OneDriveen (Suositeltu)

Lisää GitHub Actioniin:

```yaml
- name: Upload to OneDrive
  run: |
    python scripts/upload_to_onedrive.py
```

Luo `scripts/upload_to_onedrive.py`:

```python
"""Upload generated insights to OneDrive."""

import os
from app.services.onedrive_client import OneDriveClient
from pathlib import Path

def upload():
    client = OneDriveClient()
    
    # Upload today's insight
    today = datetime.now().strftime("%Y-%m-%d")
    insight_file = f"data/daily_insights/{today}.json"
    
    if Path(insight_file).exists():
        client.read_file(f"/Daily Insights/{today}.json", insight_file)
        print(f"✓ Uploaded to OneDrive")
```

✅ Etu: Ei GitHub repo-koon rajoitusta
✅ Etu: OneDrive-käyttöliittymässä näkyvissä
✅ Etu: Automaattinen versiointi
✅ Etu: M365-integraatio

---

## 🔑 OpenAI-kustannukset

Huomaa: OpenAI-kutsut **maksetaan** erillisenä:

Per päivä:
- Reader Agent: ~300 tokens = €0.0003
- Reflection Agent: ~600 tokens = €0.0006
- Coach Agent: ~400 tokens = €0.0004
- **Yhteensä päivä**: ~€0.0013

**Vuodessa**: €0.0013 × 365 = **€0.47/vuosi**

💡 Maksuissa pysyt halvalla gpt-4o-mini:llä!

---

## 💰 Kokonaisbudjetit

| Komponentti | Hinta |
|------------|-------|
| GitHub (Actions + Pages) | **€0** |
| OpenAI (päivittäin) | **€0.47/vuosi** |
| Domain (valinnainen) | **€5-10/vuosi** |
| **Yhteensä** | **€5-10/vuosi** 🎉 |

---

## 📋 Tarkistuslista

- [ ] GitHub-tili luotu
- [ ] Repository kloonattu/luotu
- [ ] `.github/workflows/daily-insight.yml` luotu
- [ ] `scripts/generate_insight.py` luotu
- [ ] GitHub Secrets asetettu (OPENAI_API_KEY)
- [ ] GitHub Pages otettu käyttöön
- [ ] Ensimmäinen ajo testattu (workflow_dispatch)
- [ ] Domain ostettu (valinnainen)
- [ ] DNS konfiguroitu

---

## 🧪 Testaus

### Suorita manuaalisesti:
1. Repository → Actions
2. Daily Insight Generator
3. "Run workflow" → Run workflow

Näet lokit ja tulokset!

### Tarkista tulokset:
- `https://yourusername.github.io/daily-insights/` tai
- `https://daily-insights.com` (jos domain konfiguroitu)

---

## 🚨 Vikadiagnosa

**Workflow epäonnistuu?**
- Actions → Daily Insight Generator → Last run
- Klikkaa → "Logs" näkee virheilmoitukset

**"OpenAI API key not found"?**
- Settings → Secrets and variables → Actions
- Varmista `OPENAI_API_KEY` on asetettu

**GitHub Pages ei näy?**
- Settings → Pages
- Tarkista branch on `main` ja folder on `/`
- Odota 1-2 minuuttia

**OneDrive-upload epäonnistuu?**
- Tarkista AZURE_* Secrets asetettu oikein
- Tarkista OneDrive-kansio `/Daily Insights` on olemassa

---

## 🎉 Lopputulos

Saat **täysin automaattisen** päivittäisen analyysin:
- ✅ €0-10/vuosi hinnalla
- ✅ 24/7 saatavilla
- ✅ Paikallinen kone voi olla sammutettuna
- ✅ Tiedot tallentuvat OneDriveen
- ✅ Linkki: `https://daily-insights.com`

Mitään ei tarvitse tehdä päivittäin - GitHub Actions hoitaa kaiken! 🤖

---

## 📝 Seuraavat askeleet

1. Katso kohdat 1-5 yllä (GitHub setup)
2. Luodaan `.github/workflows/daily-insight.yml`
3. Luodaan `scripts/generate_insight.py`
4. Aseta GitHub Secrets
5. Testaa workflow manuaalisesti
6. Hanki domain (valinnainen) → DNS setup

