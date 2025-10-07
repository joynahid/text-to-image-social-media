from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from playwright.async_api import async_playwright
from contextlib import asynccontextmanager
import asyncio
import os

# Global browser instance for reuse
browser_instance = None
playwright_instance = None
browser_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup: Initialize browser
    await get_browser()
    yield
    # Shutdown: Close browser
    global browser_instance, playwright_instance
    try:
        if browser_instance:
            await browser_instance.close()
    except Exception:
        pass  # Browser may already be closed
    try:
        if playwright_instance:
            await playwright_instance.stop()
    except Exception:
        pass  # Playwright may already be stopped


app = FastAPI(title="HTML to Image Generator", lifespan=lifespan)
router = APIRouter()


async def get_browser():
    """Get or create browser instance"""
    global browser_instance, playwright_instance
    async with browser_lock:
        if browser_instance is None:
            playwright_instance = await async_playwright().start()
            browser_instance = await playwright_instance.chromium.launch(
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    return browser_instance


def create_html_template(content: str, width: int, height: int, font_size: int, padding: int) -> str:
    """
    Create HTML template with the given content and styling.
    
    Supports full HTML/CSS for maximum control:
    - <b>, <strong> for bold
    - <i>, <em> for italic
    - <br> for line breaks
    - <p> for paragraphs
    - <span style="..."> for custom styling
    - And any other HTML/CSS you want!
    """
    # Get absolute path to fonts
    font_dir = os.path.abspath("fonts")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'Manrope';
                src: url('file://{font_dir}/Manrope-ExtraLight.ttf') format('truetype');
                font-weight: 200;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'Manrope';
                src: url('file://{font_dir}/Manrope-Light.ttf') format('truetype');
                font-weight: 300;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'Manrope';
                src: url('file://{font_dir}/Manrope-Regular.ttf') format('truetype');
                font-weight: 400;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'Manrope';
                src: url('file://{font_dir}/Manrope-Bold.ttf') format('truetype');
                font-weight: 700;
                font-style: normal;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            html, body {{
                width: {width}px;
                height: {height}px;
                overflow: hidden;
                background: linear-gradient(180deg, rgb(30, 30, 30) 0%, rgb(0, 0, 0) 100%);
            }}
            
            body {{
                color: white;
                font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: {font_size}px;
                font-weight: 200;
                line-height: 1.4;
                word-wrap: break-word;
                overflow-wrap: break-word;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                text-rendering: optimizeLegibility;
                font-smooth: always;
            }}
            
            .content {{
                padding: {padding}px;
                width: {width}px;
                height: {height}px;
                box-sizing: border-box;
                background: linear-gradient(180deg, rgb(30, 30, 30) 0%, rgb(0, 0, 0) 100%);
            }}
            
            p {{
                margin-bottom: 0.8em;
            }}
            
            p:last-child {{
                margin-bottom: 0;
            }}
            
            b, strong {{
                font-weight: bold;
            }}
            
            i, em {{
                font-style: italic;
            }}
            
            hr {{
                border: none;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                margin: 1.5em 0;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {content}
        </div>
    </body>
    </html>
    """


@router.get("/")
async def generate_image(
    text: str = Query(
        default="Hello, <b>World</b>!", 
        description="HTML content to render (supports <b>, <i>, <p>, <br>, <span>, etc.)"
    ),
    width: int = Query(default=800, description="Image width in pixels"),
    height: int = Query(default=1000, description="Image height in pixels"),
    font_size: int = Query(default=36, description="Font size in pixels"),
    padding: int = Query(default=20, description="Padding in pixels"),
):
    """
    Generate a high-quality PNG image from HTML content.
    
    Renders at 2x resolution for crisp, high-quality text.

    Parameters:
    - text: HTML content to display (supports full HTML/CSS)
    - width: Image width in pixels (output size)
    - height: Image height in pixels (output size)
    - font_size: Base font size (default: 36)
    - padding: Padding around content (default: 20)
    
    HTML Examples:
    - Bold: "This is <b>bold</b> text"
    - Italic: "This is <i>italic</i> text"
    - Combined: "This is <b><i>bold italic</i></b>"
    - Paragraphs: "<p>First paragraph</p><p>Second paragraph</p>"
    - Line breaks: "Line one<br>Line two"
    - Custom styling: "<span style='color: #ff0000;'>Red text</span>"
    """
    try:
        # Render at 2x resolution for high quality
        scale = 2
        render_width = width * scale
        render_height = height * scale
        render_font_size = font_size * scale
        render_padding = padding * scale
        
        # Create HTML from template with scaled dimensions
        html_content = create_html_template(
            text, 
            render_width, 
            render_height, 
            render_font_size, 
            render_padding
        )
        
        # Get browser instance
        browser = await get_browser()
        
        # Create a new page with scaled viewport and high DPI
        page = await browser.new_page(
            viewport={"width": render_width, "height": render_height},
            device_scale_factor=2  # 2x device pixel ratio for smooth rendering
        )
        
        try:
            # Set content and wait for it to load
            await page.set_content(html_content, wait_until="networkidle")
            
            # Wait a bit for fonts to fully render
            await page.wait_for_timeout(100)
            
            # Take screenshot at high resolution with quality settings
            screenshot_bytes = await page.screenshot(
                type="png",
                full_page=False,
                animations="disabled",  # Disable animations for consistent output
            )
            
            return Response(
                content=screenshot_bytes,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Disposition": "inline",
                },
            )
        finally:
            # Always close the page to free resources
            await page.close()

    except Exception as e:
        return Response(
            content=f'{{"error": "{str(e)}"}}',
            status_code=500,
            media_type="application/json",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HTML to Image Generator API"}


# Include router with /image-api prefix
app.include_router(router, prefix="/image-api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
