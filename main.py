from fastapi import FastAPI, Query
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = FastAPI(title="Text to Image Generator")

# Font path
FONT_PATH = "fonts/Manrope-Bold.ttf"


def clean_text(text: str) -> str:
    """Remove or replace problematic characters"""
    cleaned = "".join(char for char in text if ord(char) < 128 or char.isspace())
    return cleaned.strip()


@app.get("/")
async def generate_image(
    text: str = Query(
        default="Hello, World!", description="Text to render on the image"
    ),
    width: int = Query(default=800, description="Image width in pixels"),
    height: int = Query(default=1000, description="Image height in pixels"),
    font_size_q: int = Query(default=36, description="Font size in pixels"),
    padding_q: int = Query(default=20, description="Padding in pixels"),
):
    """
    Generate a high-quality PNG image with text on a black background.

    Parameters:
    - text: The text to display (ASCII characters only)
    - width: Image width (default: 800)
    - height: Image height (default: 1000, 4:5 ratio)
    """
    try:
        # Clean text to ASCII only
        text = clean_text(text)

        # If text is empty after cleaning, use default
        if not text:
            text = "Hello, World!"

        # Create a high-resolution image (2x for better quality)
        scale = 2
        scaled_width = width * scale
        scaled_height = height * scale

        # Create image with RGB mode and gradient background
        img = Image.new("RGB", (scaled_width, scaled_height), color=(0, 0, 0))

        # Create gradient more efficiently
        pixels = []
        for y in range(scaled_height):
            fade_factor = y / scaled_height
            gray_value = int(30 * (1 - fade_factor))
            pixels.extend([gray_value, gray_value, gray_value] * scaled_width)

        img.putdata(list(zip(pixels[::3], pixels[1::3], pixels[2::3])))

        draw = ImageDraw.Draw(img)

        # Load font at scaled size
        font_size = font_size_q * scale
        padding = padding_q * scale

        # Try to load Manrope font
        font = None
        font_paths = [
            FONT_PATH,
            "fonts/Manrope-Variable.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            except Exception:
                continue

        if font is None:
            # Use default font as last resort
            font = ImageFont.load_default()

        # Draw text with anti-aliasing
        draw.text((padding, padding), text, fill=(255, 255, 255), font=font)

        # Scale down for anti-aliasing effect
        img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Convert image to PNG bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG", quality=95)
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Text to Image Generator API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
