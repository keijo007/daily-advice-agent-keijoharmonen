# 🗑️ Poistettavat tiedostot

Seuraavat tiedostot ovat ylimääräisiä ja voidaan poistaa (vain GitHub Actions tarvitaan):

## Poista nämä tiedostot VS Codesta:

1. **CLOUD_DEPLOYMENT.md** - Azure-dokumentaatio (ei enää tarpeen)
2. **CLOUD_SETUP_QUICK.md** - Azure quick start (ei enää tarpeen)
3. **Procfile** - Heroku-konfiguraatio (ei tarpeen)
4. **requirements-cloud.txt** - Azure-riippuvuudet (ei tarpeen)

## Pidetään nämä:

✅ `README.md` - Pääohje (päivitetty)
✅ `BUDGET_DEPLOYMENT.md` - GitHub Actions -opas
✅ `requirements.txt` - Normaalit riippuvuudet
✅ `.github/workflows/daily-insight.yml` - GitHub Actions
✅ `scripts/generate_insight.py` - Pääskripti
✅ `scripts/upload_to_onedrive.py` - Valinnainen OneDrive
✅ `.github/README.md` - GitHub Actions ohjeet

---

## Poisto PowerShellissä:

```powershell
Remove-Item "CLOUD_DEPLOYMENT.md" -Force
Remove-Item "CLOUD_SETUP_QUICK.md" -Force
Remove-Item "Procfile" -Force
Remove-Item "requirements-cloud.txt" -Force
```

Tai poista manuaalisesti VS Codessa (right-click → Delete).

---

## Seuraavat askeleet:

1. Poista 4 tiedostoa
2. Push GitHubiin: `git add -A && git commit -m "cleanup: remove unnecessary cloud files" && git push`
3. Valmis! Käytössä vain GitHub Actions.
