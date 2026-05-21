"""
Generate daily insight and create HTML page for GitHub Pages.

This script:
1. Runs the daily pipeline
2. Creates beautiful HTML from the insight
3. Saves as index.html for GitHub Pages
4. Saves JSON for data archiving
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_pipeline import DailyPipeline


def generate_html(insight_data):
    """
    Create beautiful HTML page from insight data.
    
    Args:
        insight_data: Dictionary with insight data
    
    Returns:
        HTML string
    """
    
    # Safe extract helper
    def safe_get(d, key, default=""):
        if not d:
            return default
        if isinstance(d, dict):
            return d.get(key, default)
        return default
    
    # Format warnings/lists
    warnings = safe_get(insight_data, 'warnings', [])
    if isinstance(warnings, list):
        warnings_html = "\n".join([f"<li>{w}</li>" for w in warnings])
    else:
        warnings_html = f"<li>{warnings}</li>"
    
    # Extract data safely
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
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .date {{
            color: #7f8c8d;
            font-size: 0.95em;
            margin-bottom: 30px;
            text-align: center;
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
            font-size: 1.05em;
            color: #2c3e50;
        }}
        
        .warning {{
            background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%);
            border-left: 5px solid #f39c12;
            padding: 20px;
            margin: 15px 0;
            border-radius: 6px;
        }}
        
        .warning ul {{
            list-style: none;
            padding-left: 20px;
        }}
        
        .warning li {{
            color: #2c3e50;
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }}
        
        .warning li:before {{
            content: "⚠️";
            position: absolute;
            left: 0;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
        }}
        
        .confidence {{
            display: inline-block;
            background: #2ecc71;
            color: white;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-left: 10px;
        }}
        
        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .section h2 {{
                font-size: 1.4em;
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
            <div class="date">
                📅 {date_str}
            </div>
            
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
                <div class="tip">
                    {practical_tip}
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 Toimintaohje</h2>
                <p>{one_day_action}</p>
            </div>
            
            <div class="section">
                <h2>⚠️ Huomioitavaa</h2>
                <div class="warning">
                    <ul>
                        {warnings_html}
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generoitu automaattisesti GitHub Actions:lla</p>
            <p>
                <a href="https://github.com" style="color: #667eea; text-decoration: none;">
                    Näytä data →
                </a>
            </p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    """Generate insight and save as HTML + JSON."""
    
    print("\n" + "="*60)
    print("🚀 DAILY INSIGHT GENERATOR (GitHub Actions)")
    print("="*60 + "\n")
    
    try:
        # Run the pipeline
        print("⏳ Running daily pipeline...")
        pipeline = DailyPipeline()
        insight = pipeline.run()
        
        if not insight:
            print("✗ Failed to generate insight")
            sys.exit(1)
        
        # Create output directory
        output_dir = Path("data/daily_insights")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Save as JSON
        json_file = output_dir / f"{today}.json"
        
        # Convert insight to dict if it's an object
        if hasattr(insight, '__dict__'):
            insight_dict = insight.__dict__
        else:
            insight_dict = insight if isinstance(insight, dict) else {}
        
        json_file.write_text(
            json.dumps(insight_dict, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"✓ Saved JSON: {json_file}")
        
        # Generate and save HTML
        html_content = generate_html(insight_dict)
        
        # Save as today's HTML
        html_file = output_dir / f"{today}.html"
        html_file.write_text(html_content, encoding="utf-8")
        print(f"✓ Saved HTML: {html_file}")
        
        # Update index.html (latest)
        index_file = Path("index.html")
        index_file.write_text(html_content, encoding="utf-8")
        print(f"✓ Updated index.html")
        
        print("\n" + "="*60)
        print(f"✓ SUCCESS - Insight generated for {today}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
