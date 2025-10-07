from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from html2image import Html2Image
from PIL import Image
from io import BytesIO
import os
import tempfile

app = FastAPI(title="HTML to Image Generator")

router = APIRouter()


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
                src: url('file://{font_dir}/Manrope-Regular.ttf') format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'Manrope';
                src: url('file://{font_dir}/Manrope-Bold.ttf') format('truetype');
                font-weight: bold;
                font-style: normal;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            html {{
                width: {width}px;
                height: {height}px;
                background: linear-gradient(180deg, rgb(30, 30, 30) 0%, rgb(0, 0, 0) 100%);
            }}
            
            body {{
                width: {width}px;
                height: {height}px;
                background: linear-gradient(180deg, rgb(30, 30, 30) 0%, rgb(0, 0, 0) 100%);
                color: white;
                font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: {font_size}px;
                font-weight: 300;
                padding: {padding}px;
                line-height: 1.4;
                letter-spacing: -0.03em;
                overflow: hidden;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            
            .content {{
                width: 100%;
                height: auto;
                max-height: 100%;
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

    Parameters:
    - text: HTML content to display (supports full HTML/CSS)
    - width: Image width (default: 800)
    - height: Image height (default: 1000)
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
        # Create HTML from template
        html_content = create_html_template(text, width, height, font_size, padding)
        
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize Html2Image with Chrome flags for containerized environments
            hti = Html2Image(
                output_path=temp_dir,
                size=(width, height),
                custom_flags=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--headless',
                ]
            )
            
            # Generate image
            output_file = "output.png"
            result = hti.screenshot(
                html_str=html_content,
                save_as=output_file,
                size=(width, height)
            )
            
            # Read the generated image
            # html2image returns a list of filenames
            if result and len(result) > 0:
                image_path = os.path.join(temp_dir, result[0])
            else:
                image_path = os.path.join(temp_dir, output_file)
            
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Screenshot was not generated at {image_path}")
            
            # Open with PIL and convert to bytes
            with Image.open(image_path) as img:
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format="PNG")
                img_byte_arr.seek(0)
                
                return Response(
                    content=img_byte_arr.getvalue(),
                    media_type="image/png",
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Content-Disposition": "inline",
                    },
                )

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
