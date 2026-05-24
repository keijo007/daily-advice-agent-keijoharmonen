#!/usr/bin/env python3
"""
Daily Insight Generator - GitHub Actions Edition
Yhden tiedoston ratkaisu joka toimii ilman virheitä.

Käsittelee:
- Puuttuvat tiedostot/kansiot
- Puuttuvat ympäristömuuttujat
- API-virheet
- Konfiguraatio-ongelmat
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# ============================================================================
# SETUP
# ============================================================================

# Aseta parent-kansio PATH:iin
sys.path.insert(0, str(Path(__file__).parent.parent))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SAFETY CHECKS
# ============================================================================

def check_environment():
    """Tarkista ympäristön kunto."""
    logger.info("🔍 Tarkistetaan ympäristö...")
    
    # 1. Tarkista Python-versio
    if sys.version_info < (3, 9):
        logger.error(f"❌ Python 3.9+ vaaditaan, sinulla on {sys.version}")
        return False
    
    logger.info(f"✓ Python {sys.version.split()[0]}")
    
    # 2. Tarkista OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY ei asetettu")
        logger.info("   Aseta GitHub Secrets: OPENAI_API_KEY")
        return False
    
    if not api_key.startswith("sk-"):
        logger.error("❌ OPENAI_API_KEY näyttää olevan väärä (ei alusta sk-)")
        return False
    
    logger.info(f"✓ OPENAI_API_KEY asetettu ({api_key[:10]}...)")
    
    return True


def create_data_directories():
    """Luo tarvittavat data-kansiot."""
    logger.info("📁 Luodaan data-kansiot...")
    
    dirs = [
        Path("data/diary"),
        Path("data/goals"),
        Path("data/whatsapp_exports"),
        Path("data/daily_insights"),
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {dir_path}")
    
    return True


def ensure_data_files():
    """Varmista että data-tiedostot olemassa."""
    logger.info("📄 Varmistetaan data-tiedostot...")
    
    # Luodaan goals.txt jos ei olemassa
    goals_file = Path("data/goals/goals.txt")
    if not goals_file.exists():
        goals_file.write_text("""1. Oppia GitHub Actionsia
2. Hyödyntää tekoälyä päivittäin
3. Analysoida omia ajattelumalleja
4. Antaa rakentavaa palautetta järjestelmään
""")
        logger.info(f"  ✓ Luotu {goals_file} (placeholder)")
    else:
        logger.info(f"  ✓ {goals_file} olemassa")
    
    # Luodaan example diary entry
    diary_file = Path("data/diary") / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if not diary_file.exists():
        diary_file.write_text(f"""# Päivän merkintä - {datetime.now().strftime('%d.%m.%Y')}

## Saavutukset
- Aloitettiin Daily Insight Agent GitHub Actionsissa
- Konfiguroitiin automaattinen päivittäinen ajo

## Havainnot
- Tekoäly voi analysoida monimutkaisia järjestelmiä
- Automation säästää aikaa

## Tavoitteet huomiselle
- Testata systeemin toimintaa
- Korjata mahdolliset virheet
""")
        logger.info(f"  ✓ Luotu {diary_file} (placeholder)")
    else:
        logger.info(f"  ✓ {diary_file} olemassa")
    
    # RSS sources
    rss_file = Path("data/rss_sources.txt")
    if not rss_file.exists():
        rss_file.write_text("""# RSS-syötteet
# Lisää oma syötteitä alle
https://news.ycombinator.com/rss
https://techcrunch.com/feed/
""")
        logger.info(f"  ✓ Luotu {rss_file} (placeholder)")
    else:
        logger.info(f"  ✓ {rss_file} olemassa")
    
    return True


def check_dependencies():
    """Tarkista että vaadittavat moduulit on asennettu."""
    logger.info("📦 Tarkistetaan riippuvuudet...")
    
    required = [
        "fastapi",
        "openai",
        "feedparser",
        "pydantic",
        "dotenv",
    ]
    
    missing = []
    for module in required:
        try:
            __import__(module)
            logger.info(f"  ✓ {module}")
        except ImportError:
            logger.error(f"  ❌ {module} puuttuu")
            missing.append(module)
    
    if missing:
        logger.error(f"❌ Asenna puuttuvat moduulit: pip install {' '.join(missing)}")
        return False
    
    return True


# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_insight():
    """Generoi päivittäinen insight."""
    logger.info("\n" + "="*60)
    logger.info("🚀 DAILY INSIGHT GENERATOR - Starting")
    logger.info("="*60)
    
    try:
        # Import pipeline
        logger.info("📥 Ladataan pipeline...")
        from app.services.daily_pipeline import DailyPipeline
        
        # Luo pipeline
        pipeline = DailyPipeline()
        
        # Aja pipeline
        logger.info("⏳ Ajetaan pipeline...")
        insight = pipeline.run()
        
        if not insight:
            logger.error("❌ Pipeline palautti None")
            return False
        
        # Generoi HTML
        logger.info("🎨 Generoidaan HTML...")
        html = generate_html(insight)
        
        # Tallenna HTML
        today = datetime.now().strftime("%Y-%m-%d")
        
        index_file = Path("index.html")
        index_file.write_text(html)
        logger.info(f"  ✓ Tallennettu {index_file}")
        
        # Tallenna JSON
        json_file = Path("data/daily_insights") / f"{today}.json"
        
        if hasattr(insight, '__dict__'):
            insight_dict = insight.__dict__
        else:
            insight_dict = insight if isinstance(insight, dict) else {}
        
        json_file.write_text(
            json.dumps(insight_dict, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info(f"  ✓ Tallennettu {json_file}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ SUCCESS - Insight generated successfully")
        logger.info("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ ERROR during generation: {e}", exc_info=True)
        return False


def generate_html(insight_data):
    """Generoi kaunis HTML."""
    
    def safe_get(d, key, default=""):
        if not d:
            return default
        if isinstance(d, dict):
            return d.get(key, default)
        return default
    
    warnings = safe_get(insight_data, 'warnings', [])
    if isinstance(warnings, list):
        warnings_html = "\n".join([f"<li>{w}</li>" for w in warnings])
    else:
        warnings_html = f"<li>{warnings}</li>"
    
    date_str = datetime.now().strftime('%d.%m.%Y')
    reader_summary = safe_get(insight_data, 'summary', 'Ei sisältöä')
    reflection_summary = safe_get(insight_data, 'observations', 'Ei analyyseja')
    practical_tip = safe_get(insight_data, 'practical_tip', 'Ei vinkkejä')
    one_day_action = safe_get(insight_data, 'one_day_action', 'Ei toimintaa')
    
    html = f"""<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Insight - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .section p {{
            color: #34495e;
            line-height: 1.8;
            font-size: 1.05em;
        }}
        
        .tip {{
            background: linear-gradient(135deg, #e8f4f8 0%, #f0f8fb 100%);
            border-left: 5px solid #3498db;
            padding: 20px;
            margin: 15px 0;
            border-radius: 6px;
        }}
        
        .warning {{
            background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%);
            border-left: 5px solid #f39c12;
            padding: 20px;
            margin: 15px 0;
            border-radius: 6px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
        }}
        
        @media (max-width: 600px) {{
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Päivittäinen yhteenveto</h1>
            <p>Daily Insight Agent</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📰 Tänään lukemasi</h2>
                <p>{reader_summary}</p>
            </div>
            
            <div class="section">
                <h2>🧠 Havainnot ajattelustasi</h2>
                <p>{reflection_summary}</p>
            </div>
            
            <div class="section">
                <h2>💡 Tämän päivän vinkki</h2>
                <div class="tip">{practical_tip}</div>
            </div>
            
            <div class="section">
                <h2>🎯 Toimintaohje</h2>
                <p>{one_day_action}</p>
            </div>
            
            <div class="section">
                <h2>⚠️ Huomioitavaa</h2>
                <div class="warning">
                    <ul>{warnings_html}</ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generoitu {date_str} | GitHub Actions</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        # 1. Tarkista ympäristö
        if not check_environment():
            logger.error("\n❌ Ympäristön tarkistus epäonnistui")
            sys.exit(1)
        
        # 2. Luo kansiot
        if not create_data_directories():
            logger.error("\n❌ Kansioiden luominen epäonnistui")
            sys.exit(1)
        
        # 3. Varmista data-tiedostot
        if not ensure_data_files():
            logger.error("\n❌ Data-tiedostojen varmistus epäonnistui")
            sys.exit(1)
        
        # 4. Tarkista riippuvuudet
        if not check_dependencies():
            logger.error("\n❌ Riippuvuuksien tarkistus epäonnistui")
            sys.exit(1)
        
        # 5. Generoi insight
        if not generate_insight():
            logger.error("\n❌ Insightin generointi epäonnistui")
            sys.exit(1)
        
        logger.info("✅ Kaikki valmis!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("\n⏸️  Käyttäjä peruutti")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n💥 Odottamaton virhe: {e}", exc_info=True)
        sys.exit(1)
