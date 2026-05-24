"""
FastAPI web application for Daily Insight Agent.

WHY THIS FILE EXISTS:
- Provides web interface to view daily insights
- Allows manual refresh/triggering of pipeline
- Can be deployed to free cloud services (Render, Railway, Fly.io)
- Mobile-friendly for viewing on phone

ENDPOINTS:
- GET /  →  Display today's insight as HTML
- GET /api/insight  →  Return today's insight as JSON
- POST /refresh  →  Manually run the pipeline
- GET /history  →  Show past insights
- GET /sources  →  Show available data sources

DEPLOYMENT:
- Run locally: python -m uvicorn app.main:app --reload
- Deploy to cloud: Render, Railway, Fly.io all support FastAPI
- Mobile shortcut: Add web app to home screen

LAZY GENERATION:
- When user opens page, check if today's insight exists
- If not, run pipeline automatically
- If yes, show cached result
- POST /refresh allows manual re-run

ARCHITECTURE NOTES:
- FastAPI is lightweight and fast
- async/await support for scalability
- Auto-generated OpenAPI docs at /docs
- CORS enabled for mobile access
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services.daily_pipeline import DailyPipeline
from app.services.storage import StorageService
from app.config import config

# Create FastAPI app
app = FastAPI(
    title="Daily Insight Agent",
    description="Your personal AI coach that provides daily insights",
    version="1.0.0",
)

# Global pipeline instance
pipeline: Optional[DailyPipeline] = None


@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize pipeline on startup.\"\"\"
    global pipeline
    pipeline = DailyPipeline()
    print("✓ Application startup complete")


@app.get("/", response_class=HTMLResponse)
async def get_today_insight():
    \"\"\"
    Get today's insight as HTML page.
    
    Shows today's daily insight in a beautiful, readable format.
    If today's insight doesn't exist, generates it automatically.
    \"\"\"
    
    # Connect to storage
    storage = StorageService(config.DB_PATH)
    storage.connect()
    
    try:
        # Check if today's insight exists
        today_insight = storage.get_today_insight()
        
        if not today_insight:
            # No insight for today, generate one
            print("ℹ️  No insight for today, generating now...")
            global pipeline
            if pipeline is None:
                pipeline = DailyPipeline()
            
            today_insight = pipeline.run()
            
            if not today_insight:
                return _error_html("Unable to generate today's insight. Check logs.")
        
        # Render HTML
        html = _render_insight_html(today_insight)
        return html
    
    finally:
        storage.disconnect()


@app.get("/api/insight")
async def api_get_today_insight():
    \"\"\"
    Get today's insight as JSON.
    
    Useful for integrations or programmatic access.
    \"\"\"
    
    storage = StorageService(config.DB_PATH)
    storage.connect()
    
    try:
        today_insight = storage.get_today_insight()
        
        if not today_insight:
            global pipeline
            if pipeline is None:
                pipeline = DailyPipeline()
            
            today_insight = pipeline.run()
        
        if today_insight:
            return JSONResponse(today_insight.to_dict())
        else:
            return JSONResponse({"error": "Unable to generate insight"}, status_code=500)
    
    finally:
        storage.disconnect()


@app.post("/refresh")
async def refresh_insight(background_tasks: BackgroundTasks):
    \"\"\"
    Manually trigger pipeline to generate new insight.
    
    Runs in background so response is quick.
    \"\"\"
    
    global pipeline
    if pipeline is None:
        pipeline = DailyPipeline()
    
    # Run pipeline in background
    background_tasks.add_task(pipeline.run)
    
    return {
        "status": "running",
        "message": "Pipeline started in background. Refresh page in a moment."
    }


@app.get("/history")
async def get_history():
    \"\"\"Get list of past insights.\"\"\"
    
    # For now, return simple page
    # Could enhance to show calendar/timeline of insights
    
    html = \"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <title>Insight History</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            p { color: #666; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>📚 Insight History</h1>
        <p>Feature coming soon! This will show all your past daily insights.</p>
        <p><a href="/">← Back to today</a></p>
    </body>
    </html>
    \"\"\"
    
    return HTMLResponse(html)


@app.get("/sources")
async def get_sources():
    \"\"\"Show configured data sources.\"\"\"
    
    html = \"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Sources</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            .source { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .source h3 { margin: 0 0 5px 0; }
            .source p { margin: 0; color: #666; font-size: 14px; }
            a { color: #0066cc; }
        </style>
    </head>
    <body>
        <h1>📊 Data Sources</h1>
        <p>The Daily Insight Agent reads from these sources:</p>
        
        <div class="source">
            <h3>📖 Diary</h3>
            <p>Your personal diary entries from <code>data/diary/</code></p>
        </div>
        
        <div class="source">
            <h3>🎯 Goals</h3>
            <p>Your personal goals from <code>GOALS_FILE_PATH</code> (.env)</p>
        </div>
        
        <div class="source">
            <h3>📰 RSS Feeds</h3>
            <p>Articles from RSS feeds listed in <code>data/rss_sources.txt</code></p>
        </div>
        
        <div class="source">
            <h3>💬 WhatsApp (Coming Soon)</h3>
            <p>Summaries of exported WhatsApp conversations</p>
        </div>
        
        <div class="source">
            <h3>📺 YouTube (Coming Soon)</h3>
            <p>Transcripts from your watched videos</p>
        </div>
        
        <div class="source">
            <h3>✈️ Telegram (Coming Soon)</h3>
            <p>Messages from Telegram channels</p>
        </div>
        
        <p><a href="/">← Back to today</a></p>
    </body>
    </html>
    \"\"\"
    
    return HTMLResponse(html)


@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint for deployment monitoring.\"\"\"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Helper functions for rendering HTML
# ============================================================================

def _render_insight_html(insight) -> str:
    \"\"\"Render DailyInsight as beautiful HTML page.\"\"\"
    
    quotes_html = ""
    for quote_obj in insight.important_quotes:
        if isinstance(quote_obj, dict):
            quote = quote_obj.get("quote", "")
            source = quote_obj.get("source", "Unknown")
        else:
            quote = str(quote_obj)
            source = "Unknown"
        
        quotes_html += f'<blockquote>{quote}<br><small>— {source}</small></blockquote>'
    
    html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <title>Daily Insight - {insight.date}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ font-size: 32px; margin: 0 0 10px 0; }}
            .header .date {{ opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px 20px; }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ color: #667eea; font-size: 20px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            .section p {{ line-height: 1.6; color: #333; margin: 10px 0; }}
            blockquote {{ border-left: 4px solid #667eea; padding-left: 15px; margin: 15px 0; font-style: italic; color: #666; }}
            blockquote small {{ display: block; font-style: normal; color: #999; margin-top: 5px; }}
            .action-box {{ background: #f0f4ff; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .warning {{ background: #fff5f5; border-left: 4px solid #e53e3e; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .footer {{ background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
            .button {{ display: inline-block; margin: 10px 5px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; font-size: 14px; }}
            .button:hover {{ background: #5568d3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 Daily Insight</h1>
                <div class="date">{insight.date}</div>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>📌 Main Insight</h2>
                    <p>{insight.main_insight}</p>
                </div>
                
                <div class="section">
                    <h2>📰 Today's Content Summary</h2>
                    <p>{insight.source_summary}</p>
                </div>
                
                <div class="section">
                    <h2>🔍 Self-Reflection</h2>
                    <p>{insight.self_reflection}</p>
                </div>
                
                {f'<div class="section"><h2>⚠️ Thinking Patterns</h2><ul>{"".join([f"<li>{bias}</li>" for bias in insight.thinking_biases_detected])}</ul></div>' if insight.thinking_biases_detected else ''}
                
                <div class="action-box">
                    <h2>✅ Action for Today</h2>
                    <p><strong>{insight.one_day_action}</strong></p>
                    <p style="margin-top: 10px; font-size: 14px; color: #666;">{insight.practical_tip}</p>
                </div>
                
                {f'<div class="section"><h2>💡 Project Idea</h2><p>{insight.possible_project_idea}</p></div>' if insight.possible_project_idea else ''}
                
                {f'<div class="section"><h2>📖 Key Quotes</h2>{quotes_html}</div>' if insight.important_quotes else ''}
                
                {f'<div class="warning"><strong>Uncertainties:</strong><ul>{"".join([f"<li>{u}</li>" for u in insight.uncertainties])}</ul></div>' if insight.uncertainties else ''}
            </div>
            
            <div class="footer">
                <p><strong>Sources:</strong> {', '.join(insight.sources_used)}</p>
                <p style="margin-top: 15px;"><button class="button" onclick="location.href='/refresh'">🔄 Refresh</button></p>
                <p style="margin-top: 15px; font-size: 11px; color: #bbb;">Daily Insight Agent • Made with ❤️ by AI</p>
            </div>
        </div>
    </body>
    </html>
    \"\"\"
    
    return html


def _error_html(message: str) -> str:
    \"\"\"Render error page.\"\"\"
    
    html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
            .error {{ background: #fff5f5; border-left: 4px solid #e53e3e; padding: 20px; border-radius: 4px; }}
            h1 {{ color: #e53e3e; }}
            p {{ color: #666; }}
            a {{ color: #0066cc; }}
        </style>
    </head>
    <body>
        <div class="error">
            <h1>❌ Error</h1>
            <p>{message}</p>
            <p><a href="/">← Retry</a></p>
        </div>
    </body>
    </html>
    \"\"\"
    
    return html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
