# OneDrive Integration Setup

## 📋 Overview

The Daily Insight Agent can automatically upload your daily insights to OneDrive. This allows you to:
- ☁️ Back up insights in the cloud
- 📊 Access insights from any device
- 🔄 Sync with other applications
- 📱 View on mobile via OneDrive app

## 🎯 What Gets Uploaded

Each day, the workflow uploads:
```
/DailyInsights/
  ├── 2026-05-24.json
  ├── 2026-05-25.json
  ├── 2026-05-26.json
  └── ...
```

Each JSON file contains:
- Summary of new content
- Key insights and observations
- Practical daily tips
- Detected thinking biases
- Project ideas
- And more...

## ⚙️ Setup Steps

### Step 1: Create Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com/)
2. Search for **"App registrations"** → Click **New registration**
3. Fill in:
   - **Name**: `daily-insight-agent` (or any name)
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave empty for now
4. Click **Register**

### Step 2: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `GitHub Actions`
4. Expires: `12 months` (or choose your preference)
5. Click **Add**
6. **Copy the secret value** → Store safely (you'll need it)

### Step 3: Get Your Credentials

From your app registration overview page, copy:
- **Application (client) ID** → Save as `AZURE_CLIENT_ID`
- **Directory (tenant) ID** → Save as `AZURE_TENANT_ID`
- **Client secret** from Step 2 → Save as `AZURE_CLIENT_SECRET`

### Step 4: Grant OneDrive Access

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions** (not Delegated)
5. Search for and select:
   - `Files.ReadWrite.All` (to read/write files)
6. Click **Add permissions**
7. Click **Grant admin consent for [Your Org]** (needs admin rights)

### Step 5: Add Secrets to GitHub

1. Go to your GitHub repo
2. Settings → **Secrets and variables** → **Actions**
3. Add 3 new secrets:

| Name | Value |
|------|-------|
| `AZURE_CLIENT_ID` | From Step 3 |
| `AZURE_TENANT_ID` | From Step 3 |
| `AZURE_CLIENT_SECRET` | From Step 2 |

💡 **Note**: `OPENAI_API_KEY` should already be in your secrets

### Step 6: Create Folders in OneDrive

1. Open [OneDrive](https://onedrive.live.com)
2. Create folder: `DailyInsights` (in root)
3. Optional folders:
   - `Diary` (if using diary collector)
   - `WhatsApp` (for WhatsApp exports)

## 📂 OneDrive Folder Structure

Recommended structure in your OneDrive:

```
/
  ├── DailyInsights/          ← Workflow uploads here
  │   ├── 2026-05-24.json
  │   ├── 2026-05-25.json
  │   └── ...
  │
  ├── Diary/                  ← Put your diary files here
  │   ├── 2026-05-20.md
  │   ├── 2026-05-21.md
  │   └── ...
  │
  ├── WhatsApp/               ← WhatsApp exports
  │   ├── chat_export_1.txt
  │   └── ...
  │
  └── goals.txt               ← Your goals file (root level)
```

## 🔄 How It Works

### Daily Workflow

1. **06:00 UTC** (8:00 AM Finland summer time)
2. GitHub Actions runs `generate_insight_safe.py`
3. Insight JSON is created in `data/daily_insights/`
4. Git commit & push to GitHub
5. **Optional**: Upload to OneDrive via `upload_to_onedrive.py`

### What Happens If OneDrive Upload Fails

- ✅ The workflow **does NOT fail**
- 📝 Error is logged, but workflow continues
- 💾 Your insights are still saved locally and to GitHub
- 🔄 You can retry manually

## 🛠️ Manual Upload

Run locally to test:

```bash
# Set your credentials
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Run the upload script
python scripts/upload_to_onedrive.py
```

## 📱 Accessing on Mobile

1. Install **Microsoft OneDrive** app
2. Sign in with your account
3. Navigate to `/DailyInsights/`
4. Tap any `.json` file to view/share

## 🔒 Security Notes

- ✅ Credentials stored in GitHub Secrets (encrypted)
- ✅ Never commit `.env` with credentials
- ✅ Secrets are masked in workflow logs
- ⚠️ Client Secret has expiration (default 1 year) - renew before expiry
- 🔑 Consider rotating secrets periodically

## ❌ Troubleshooting

### "OneDrive not configured"
- Check that all 3 secrets are in GitHub repo
- Verify secret names are exactly: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- Restart workflow

### "Permission denied"
- Verify **API permissions** are granted (Step 4)
- Check admin consent is applied
- Try creating a test folder in OneDrive manually first

### "File not found in DailyInsights"
- Check OneDrive folder path is exactly `/DailyInsights/`
- Create folder if missing
- Verify no typos in path

### "Workflow succeeds but upload doesn't happen"
- Check GitHub Actions log for "OneDrive not configured"
- Run `scripts/upload_to_onedrive.py` locally to debug
- Check Azure credentials are correct

## 🚀 Next Steps

After setup is complete:

1. ✅ Trigger workflow manually: **Actions** → **Daily Insight Generator** → **Run workflow**
2. ✅ Check OneDrive `/DailyInsights/` for today's file
3. ✅ Review the uploaded JSON to verify format
4. ✅ Wait for tomorrow's 06:00 UTC automatic run

## 📖 More Information

- [Microsoft Graph API Docs](https://docs.microsoft.com/en-us/graph/api/overview)
- [OneDrive API](https://docs.microsoft.com/en-us/onedrive/developer/)
- [Azure App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)

---

**Questions?** Check the main [README.md](README.md) or review the example code in [app/services/onedrive_client.py](app/services/onedrive_client.py)
