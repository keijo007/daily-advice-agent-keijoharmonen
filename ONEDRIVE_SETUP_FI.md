# OneDrive Integraatio - Opas Suomeksi 🇫🇮

## 📋 Yleiskatsaus

Workflow luo joka päivä uuden insight JSON-tiedoston ja voi ladata sen automaattisesti OneDriveen.

**Kansiorakenne OneDrivessa:**
```
/DailyInsights/
  ├── 2026-05-24.json
  ├── 2026-05-25.json
  ├── 2026-05-26.json
  └── ... (yksi per päivä)
```

## ✅ Mitä Korjattiin

### 1. **Git Push -virhe**
- ❌ Vanha: `git push` → Epäonnistui (Permission denied)
- ✅ Uusi: `git push origin main` + `GITHUB_TOKEN`
- 📍 Tiedosto: `.github/workflows/main.yml`

### 2. **OneDrive Upload**
- ➕ Lisätty `write_file()` metodi OneDriveClientille
- ➕ Päivitetty `upload_to_onedrive.py` skripti
- ✅ Nyt tiedostot latautuvat automaattisesti OneDriveen

### 3. **Workflow Sekvenssi**
Uusi järjestys:
1. ✅ Koodi checkout
2. ✅ Python setup
3. ✅ Riippuvuuksien asennus
4. ✅ Insight-geneerointi
5. ✅ Git commit & push (GITHUB_TOKEN)
6. ✅ **OneDrive upload** ← UUSI
7. ✅ Tulostus lokeihin

## 🎯 Mihin Tiedostot Menevät

### GitHub
- Lokaali: `data/daily_insights/2026-05-25.json`
- GitHub: Repository root → `data/daily_insights/`

### OneDrive
- OneDrive: `/DailyInsights/2026-05-25.json` (jos OneDrive asennettu)

### Sisältö (JSON)
Joka päivä sisältää:
- 📄 **main_insight** - Pääviesti
- 📊 **source_summary** - Lähteiden yhteenveto
- 🤔 **self_reflection** - Itsereflektio
- 🧠 **thinking_biases_detected** - Ajattelun harhat
- 💡 **practical_tip** - Käytännön vinkki
- ⚡ **one_day_action** - Tämän päivän toiminta
- 🎯 **possible_project_idea** - Projekti-idea
- 💬 **important_quotes** - Tärkeät lainaukset
- ❓ **uncertainties** - Epävarmuustekijät
- 📚 **sources_used** - Käytetyt lähteet

## 🔧 OneDrive Asennus

### Lyhyt versio (5 askelta)

1. **Azure App Registration luominen**
   - https://portal.azure.com → App registrations → New
   - Nimi: `daily-insight-agent`

2. **Client Secret luominen**
   - Certificates & secrets → New client secret
   - Copy: Secret value

3. **Credentials kerääminen**
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret (Step 2)

4. **API Permissions**
   - API permissions → Add permission → Microsoft Graph
   - Files.ReadWrite.All → Grant admin consent

5. **GitHub Secrets**
   - Settings → Secrets → New secrets:
     - `AZURE_CLIENT_ID`
     - `AZURE_CLIENT_SECRET`
     - `AZURE_TENANT_ID`

### Yksityiskohtainen opas
Katso: [ONEDRIVE_SETUP.md](ONEDRIVE_SETUP.md)

## 📁 Kansiorakenne OneDrivessa

Luo nämä kansiot OneDriveen:

```
OneDrive root (/)
├── DailyInsights/          ← Workflow lataa tämä
│   ├── 2026-05-24.json
│   ├── 2026-05-25.json
│   └── ...
│
├── Diary/                  ← Päiväkirja (valinnainen)
│   ├── 2026-05-20.md
│   ├── 2026-05-21.md
│   └── ...
│
├── WhatsApp/               ← WhatsApp-viestit (valinnainen)
│   └── chat_export.txt
│
└── goals.txt               ← Tavoitteet (root)
```

## 🤔 Usein Kysytyt

**K: Mitä tapahtuu jos OneDrive upload epäonnistuu?**
V: Workflow JATKUU normaalisti. Insights tallennetaan GitHubiin normaalisti. OneDrive on valinnainen.

**K: Kuinka usein tiedostot latautuvat?**
V: Joka päivä klo 06:00 UTC (klo 8 kesällä Suomessa, klo 9 talvella).

**K: Voinko ajaa sen manuaalisesti?**
V: Kyllä:
```bash
python scripts/upload_to_onedrive.py
```

**K: Onko tämä turvallista?**
V: Kyllä:
- Credentials tallennettu GitHub Secretsiin (salattu)
- Client Secret voi vanhentua (renew ~vuoden välein)
- Ei koskaan commitoi `.env` -tiedostoa

**K: Voinko käyttää OneDrivea ilman tätä?**
V: Kyllä, insights tallennetaan aina GitHubiin. OneDrive on valinnainen backup.

## 🚀 Seuraavat Askeleet

1. ✅ Lue [ONEDRIVE_SETUP.md](ONEDRIVE_SETUP.md) yksityiskohtaisesti
2. ✅ Suorita Azure App Registration
3. ✅ Lisää GitHub Secrets
4. ✅ Luo `/DailyInsights/` kansio OneDriveen
5. ✅ Trigger workflow manuaalisesti: Actions → Daily Insight Generator → Run workflow
6. ✅ Tarkista OneDrive `/DailyInsights/` - pitäisi näkyä JSON-tiedosto

## 🔍 Debuggaus

Katso workflow lokit:
1. GitHub repo → Actions
2. Valitse uusin "Daily Insight Generator"
3. Klikkaa "Upload to OneDrive (optional)" steppaa
4. Tarkista lokit

## 📞 Apua

Ongelmat?
- Katso [ONEDRIVE_SETUP.md](ONEDRIVE_SETUP.md) → Troubleshooting
- Tarkista GitHub Actions lokit
- Varmista Azure credentials
- Testaa `python scripts/upload_to_onedrive.py` lokaalisesti

---

**Yhteenveto:** Git push nyt toimii (GITHUB_TOKEN), ja insights latautuvat automaattisesti OneDriveen (jos asennettu). Joka päivä 06:00 UTC uusi JSON-tiedosto ilmestyy `/DailyInsights/` kansioon! 🎉
