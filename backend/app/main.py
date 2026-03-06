"""FastAPI main application"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from loguru import logger
import sys
from contextlib import asynccontextmanager

from app.config import settings
from app.database import db_manager
from app import __version__

# Import routers
from app.routers import search, import_router, entities, health


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    settings.LOG_FILE,
    rotation="100 MB",
    retention="30 days",
    level=settings.LOG_LEVEL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{__version__}")
    logger.info("Initializing database connections...")
    
    # Initialize database clients
    db_manager.get_mongodb_client()
    db_manager.get_elasticsearch_client()
    db_manager.get_neo4j_driver()
    db_manager.get_redis_client()
    
    logger.info("All database connections initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    db_manager.close_all()
    logger.info("All database connections closed")


# Create FastAPI app
app = FastAPI(
    title="🔱 OSINT TERMINAL API",
    version=__version__,
    description="""
    ╔═══════════════════════════════════════════════════════════╗
    ║  ⚡ CLASSIFIED INTELLIGENCE API ⚡                        ║
    ║  Advanced OSINT Data Aggregation & Analysis Platform     ║
    ╚═══════════════════════════════════════════════════════════╝
    
    🔍 Capabilities:
    • Multi-database intelligence search
    • Entity relationship mapping
    • Real-time data import and normalization
    • Cross-reference analysis
    • Graph-based pattern detection
    
    🛡️ Security: Offline-first, air-gapped deployment
    """,
    lifespan=lifespan,
    docs_url=None,  # Disable default docs
    redoc_url=None  # Disable redoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(entities.router, prefix="/api/v1", tags=["entities"])
app.include_router(import_router.router, prefix="/api/v1", tags=["import"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": __version__,
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with professional hacker theme"""
    custom_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>{app.title} - API TERMINAL</title>
        <style>
            /* Professional Hacker Theme for API Documentation */
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&display=swap');
            
            * {{
                font-family: 'Fira Code', 'Courier New', monospace !important;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                background: #0a0e27 !important;
                background-image: 
                    linear-gradient(0deg, transparent 24%, rgba(0, 255, 65, 0.03) 25%, rgba(0, 255, 65, 0.03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 65, 0.03) 75%, rgba(0, 255, 65, 0.03) 76%, transparent 77%, transparent),
                    linear-gradient(90deg, transparent 24%, rgba(0, 255, 65, 0.03) 25%, rgba(0, 255, 65, 0.03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 65, 0.03) 75%, rgba(0, 255, 65, 0.03) 76%, transparent 77%, transparent);
                background-size: 50px 50px;
                position: relative;
            }}
            
            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 50% 50%, rgba(0, 255, 65, 0.1) 0%, transparent 50%);
                pointer-events: none;
                z-index: 0;
            }}
            
            .swagger-ui {{
                position: relative;
                z-index: 1;
            }}
            
            /* Topbar - Professional Header */
            .swagger-ui .topbar {{
                background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0a0e27 100%) !important;
                border-bottom: 3px solid #00ff41 !important;
                box-shadow: 0 4px 30px rgba(0, 255, 65, 0.4), inset 0 1px 0 rgba(0, 217, 255, 0.2) !important;
                padding: 15px 0 !important;
            }}
            
            .swagger-ui .topbar .wrapper {{
                padding: 10px 20px;
            }}
            
            .swagger-ui .topbar a {{
                color: #00ff41 !important;
                font-weight: 700 !important;
                font-size: 24px !important;
                text-shadow: 0 0 20px rgba(0, 255, 65, 1), 0 0 40px rgba(0, 255, 65, 0.6) !important;
                letter-spacing: 2px !important;
            }}
            
            /* Info Section */
            .swagger-ui .info {{
                background: rgba(10, 14, 39, 0.9) !important;
                border: 2px solid #00ff41 !important;
                border-radius: 8px !important;
                padding: 30px !important;
                margin: 20px 0 !important;
                box-shadow: 0 0 40px rgba(0, 255, 65, 0.3), inset 0 0 20px rgba(0, 217, 255, 0.1) !important;
            }}
            
            .swagger-ui .info .title {{
                color: #00ff41 !important;
                text-shadow: 0 0 15px rgba(0, 255, 65, 0.8), 0 0 30px rgba(0, 255, 65, 0.4) !important;
                font-size: 36px !important;
                font-weight: 700 !important;
                letter-spacing: 3px !important;
                margin-bottom: 20px !important;
                border-bottom: 2px solid rgba(0, 255, 65, 0.3) !important;
                padding-bottom: 15px !important;
            }}
            
            .swagger-ui .info .description {{
                color: #00d9ff !important;
                line-height: 1.8 !important;
                font-size: 14px !important;
            }}
            
            .swagger-ui .info .description p {{
                color: #00d9ff !important;
            }}
            
            /* Scheme Container */
            .swagger-ui .scheme-container {{
                background: rgba(10, 14, 39, 0.8) !important;
                border: 1px solid #00ff41 !important;
                border-radius: 5px !important;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.2) !important;
            }}
            
            /* Operation Blocks */
            .swagger-ui .opblock-tag {{
                border-bottom: 3px solid #00ff41 !important;
                background: linear-gradient(90deg, rgba(0, 255, 65, 0.15) 0%, rgba(0, 217, 255, 0.1) 100%) !important;
                padding: 15px 20px !important;
                margin: 20px 0 10px 0 !important;
                border-radius: 5px 5px 0 0 !important;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.2) !important;
            }}
            
            .swagger-ui .opblock-tag-section {{
                margin-bottom: 30px !important;
            }}
            
            .swagger-ui .opblock-tag:hover {{
                background: linear-gradient(90deg, rgba(0, 255, 65, 0.25) 0%, rgba(0, 217, 255, 0.2) 100%) !important;
            }}
            
            .swagger-ui .opblock {{
                background: rgba(10, 14, 39, 0.95) !important;
                border: 2px solid #00ff41 !important;
                border-radius: 8px !important;
                box-shadow: 0 0 25px rgba(0, 255, 65, 0.3), inset 0 1px 0 rgba(0, 217, 255, 0.2) !important;
                margin: 15px 0 !important;
                overflow: hidden !important;
                transition: all 0.3s ease !important;
            }}
            
            .swagger-ui .opblock:hover {{
                box-shadow: 0 0 35px rgba(0, 255, 65, 0.5), 0 0 60px rgba(0, 217, 255, 0.3), inset 0 1px 0 rgba(0, 217, 255, 0.3) !important;
                transform: translateY(-2px) !important;
            }}
            
            /* HTTP Method Styling */
            .swagger-ui .opblock.opblock-get {{
                border-color: #00ff41 !important;
                background: linear-gradient(135deg, rgba(0, 255, 65, 0.08) 0%, rgba(10, 14, 39, 0.95) 100%) !important;
            }}
            
            .swagger-ui .opblock.opblock-post {{
                border-color: #00d9ff !important;
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.08) 0%, rgba(10, 14, 39, 0.95) 100%) !important;
            }}
            
            .swagger-ui .opblock.opblock-put {{
                border-color: #ffd700 !important;
                background: linear-gradient(135deg, rgba(255, 215, 0, 0.08) 0%, rgba(10, 14, 39, 0.95) 100%) !important;
            }}
            
            .swagger-ui .opblock.opblock-delete {{
                border-color: #ff0055 !important;
                background: linear-gradient(135deg, rgba(255, 0, 85, 0.08) 0%, rgba(10, 14, 39, 0.95) 100%) !important;
            }}
            
            .swagger-ui .opblock-summary-method {{
                background: linear-gradient(135deg, #00ff41 0%, #00d9ff 100%) !important;
                color: #0a0e27 !important;
                font-weight: 700 !important;
                text-shadow: none !important;
                min-width: 80px !important;
                border-radius: 5px !important;
                padding: 8px 15px !important;
                box-shadow: 0 0 15px rgba(0, 255, 65, 0.6) !important;
            }}
            
            .swagger-ui .opblock-summary-path {{
                color: #00d9ff !important;
                font-weight: 600 !important;
                text-shadow: 0 0 10px rgba(0, 217, 255, 0.5) !important;
            }}
            
            .swagger-ui .opblock-summary-description {{
                color: #a0a0a0 !important;
            }}
            
            /* Buttons */
            .swagger-ui .btn {{
                background: linear-gradient(135deg, #00ff41 0%, #00d9ff 100%) !important;
                color: #0a0e27 !important;
                border: none !important;
                font-weight: 700 !important;
                border-radius: 5px !important;
                padding: 10px 25px !important;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.6), 0 4px 15px rgba(0, 0, 0, 0.3) !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
            }}
            
            .swagger-ui .btn:hover {{
                box-shadow: 0 0 30px rgba(0, 255, 65, 0.9), 0 0 50px rgba(0, 217, 255, 0.5) !important;
                transform: translateY(-3px) !important;
            }}
            
            .swagger-ui .btn.execute {{
                background: linear-gradient(135deg, #ff0055 0%, #ff6b00 100%) !important;
                box-shadow: 0 0 20px rgba(255, 0, 85, 0.6) !important;
            }}
            
            .swagger-ui .btn.execute:hover {{
                box-shadow: 0 0 30px rgba(255, 0, 85, 0.9) !important;
            }}
            
            /* Parameters */
            .swagger-ui .parameters {{
                background: rgba(10, 14, 39, 0.6) !important;
                border: 1px solid rgba(0, 255, 65, 0.3) !important;
                border-radius: 5px !important;
                padding: 15px !important;
            }}
            
            .swagger-ui .parameter__name {{
                color: #00ff41 !important;
                font-weight: 700 !important;
            }}
            
            .swagger-ui .parameter__type {{
                color: #ffd700 !important;
                font-weight: 600 !important;
            }}
            
            .swagger-ui table thead tr th {{
                background: rgba(0, 255, 65, 0.2) !important;
                color: #00ff41 !important;
                border-color: #00ff41 !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
            }}
            
            .swagger-ui table tbody tr td {{
                color: #00d9ff !important;
                border-color: rgba(0, 255, 65, 0.2) !important;
            }}
            
            /* Response */
            .swagger-ui .responses-inner {{
                background: rgba(10, 14, 39, 0.8) !important;
                border: 1px solid rgba(0, 255, 65, 0.3) !important;
                border-radius: 5px !important;
                padding: 15px !important;
            }}
            
            .swagger-ui .response-col_status {{
                color: #00ff41 !important;
                font-weight: 700 !important;
                font-size: 16px !important;
            }}
            
            .swagger-ui .response-col_description {{
                color: #00d9ff !important;
            }}
            
            /* Code Blocks */
            .swagger-ui .highlight-code {{
                background: #0a0e27 !important;
                border: 1px solid #00ff41 !important;
                border-radius: 5px !important;
            }}
            
            .swagger-ui .highlight-code > .microlight {{
                color: #00d9ff !important;
            }}
            
            /* Models */
            .swagger-ui .model-title {{
                color: #00ff41 !important;
                font-weight: 700 !important;
            }}
            
            .swagger-ui .model {{
                background: rgba(10, 14, 39, 0.8) !important;
                border: 1px solid rgba(0, 255, 65, 0.3) !important;
                border-radius: 5px !important;
            }}
            
            .swagger-ui .model-box {{
                background: rgba(10, 14, 39, 0.9) !important;
            }}
            
            /* Input Fields */
            .swagger-ui input[type=text],
            .swagger-ui input[type=email],
            .swagger-ui input[type=password],
            .swagger-ui textarea,
            .swagger-ui select {{
                background: rgba(10, 14, 39, 0.9) !important;
                border: 2px solid #00ff41 !important;
                color: #00d9ff !important;
                border-radius: 5px !important;
                padding: 10px !important;
                box-shadow: inset 0 0 10px rgba(0, 255, 65, 0.2) !important;
            }}
            
            .swagger-ui input[type=text]:focus,
            .swagger-ui textarea:focus,
            .swagger-ui select:focus {{
                border-color: #00d9ff !important;
                box-shadow: 0 0 20px rgba(0, 217, 255, 0.5), inset 0 0 10px rgba(0, 255, 65, 0.2) !important;
                outline: none !important;
            }}
            
            /* Scrollbar */
            ::-webkit-scrollbar {{
                width: 14px;
                height: 14px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: #0a0e27;
                border: 1px solid rgba(0, 255, 65, 0.2);
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, #00ff41 0%, #00d9ff 100%);
                border-radius: 7px;
                box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: linear-gradient(135deg, #00d9ff 0%, #00ff41 100%);
            }}
            
            /* Authorization */
            .swagger-ui .auth-wrapper {{
                background: rgba(10, 14, 39, 0.9) !important;
                border: 2px solid #00ff41 !important;
                border-radius: 8px !important;
                box-shadow: 0 0 30px rgba(0, 255, 65, 0.3) !important;
            }}
            
            /* Animations */
            @keyframes glowPulse {{
                0%, 100% {{
                    box-shadow: 0 0 25px rgba(0, 255, 65, 0.3), inset 0 1px 0 rgba(0, 217, 255, 0.2);
                }}
                50% {{
                    box-shadow: 0 0 40px rgba(0, 255, 65, 0.6), 0 0 60px rgba(0, 217, 255, 0.4), inset 0 1px 0 rgba(0, 217, 255, 0.3);
                }}
            }}
            
            .swagger-ui .opblock:hover {{
                animation: glowPulse 2s infinite !important;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {{
                window.ui = SwaggerUIBundle({{
                    url: '{app.openapi_url}',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "BaseLayout",
                    persistAuthorization: true,
                    displayRequestDuration: true,
                    filter: true,
                    syntaxHighlight: {{
                        activate: true,
                        theme: "monokai"
                    }}
                }});
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=custom_html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
