from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = FastAPI(title="Text to Image Generator")

router = APIRouter()


# Font path
FONT_PATH = "fonts/Manrope-Bold.ttf"


def clean_text(text: str) -> str:
    """Remove or replace problematic characters"""
    cleaned = "".join(char for char in text if ord(char) < 128 or char.isspace())
    return cleaned.strip()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """
    Wrap text to fit within max_width by breaking at word boundaries.
    Also respects existing newline characters in the text.
    """
    lines = []
    
    # Split by existing newlines first
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            # Preserve empty lines
            lines.append('')
            continue
            
        words = paragraph.split()
        current_line = []
        
        for word in words:
            # Try adding this word to current line
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                # Line is too long, save current line and start new one
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, need to break the word
                    if word:
                        # Check if the single word fits
                        word_bbox = font.getbbox(word)
                        word_width = word_bbox[2] - word_bbox[0]
                        if word_width > max_width:
                            # Break the word character by character
                            char_line = ""
                            for char in word:
                                test_char_line = char_line + char
                                char_bbox = font.getbbox(test_char_line)
                                char_width = char_bbox[2] - char_bbox[0]
                                if char_width <= max_width:
                                    char_line = test_char_line
                                else:
                                    if char_line:
                                        lines.append(char_line)
                                    char_line = char
                            if char_line:
                                current_line = [char_line]
                        else:
                            current_line = [word]
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
    
    return lines


@router.get("/")
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

        # Calculate maximum text width
        max_text_width = scaled_width - (2 * padding)
        
        # Wrap text into multiple lines
        lines = wrap_text(text, font, max_text_width)
        
        # Calculate line height (with some spacing between lines)
        bbox = font.getbbox("Ay")  # Use a tall character to get line height
        line_height = bbox[3] - bbox[1]
        line_spacing = int(line_height * 0.3)  # 30% spacing between lines
        total_line_height = line_height + line_spacing
        
        # Draw each line of text
        y_position = padding
        for line in lines:
            draw.text((padding, y_position), line, fill=(255, 255, 255), font=font)
            y_position += total_line_height

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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Text to Image Generator API"}


# Include router with /image-api prefix
app.include_router(router, prefix="/image-api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
