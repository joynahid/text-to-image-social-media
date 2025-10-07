# Text-to-Image Generator API

A high-performance FastAPI service that generates beautiful PNG images from text with a faded dark gradient background and the Manrope font.

## Features

- ✨ **Beautiful Design** - Faded dark gradient background (dark gray to black)
- 🎨 **Manrope Font** - Modern, clean typography
- ⚡ **High Quality** - 2x supersampling with LANCZOS downscaling
- 🚀 **Fast** - Built with FastAPI and optimized image generation
- 🐳 **Docker Ready** - Easy deployment with Docker Compose
- 📱 **Flexible Dimensions** - Customizable width and height

## Quick Start

### Local Development

```bash
# Install dependencies
uv pip install fastapi pillow uvicorn

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## API Usage

### Basic Request

```bash
curl "http://localhost:8000/?text=Hello+World" -o image.png
```

### Custom Dimensions

```bash
# Square (1:1)
curl "http://localhost:8000/?text=Hello&width=1080&height=1080" -o square.png

# Instagram Story (9:16)
curl "http://localhost:8000/?text=Story&width=1080&height=1920" -o story.png

# Twitter Card (16:9)
curl "http://localhost:8000/?text=News&width=1200&height=675" -o twitter.png

# Default (4:5)
curl "http://localhost:8000/?text=Post&width=800&height=1000" -o default.png
```

### Multiline Text

```bash
curl -G "http://localhost:8000/" \
  --data-urlencode "text=Line 1
Line 2
Line 3" \
  -o multiline.png
```

### Quote Cards

```bash
curl -G "http://localhost:8000/" \
  --data-urlencode "text=The best way to predict
the future is to create it.

- Peter Drucker" \
  --data-urlencode "width=1080" \
  --data-urlencode "height=1350" \
  -o quote.png
```

## API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | `"Hello, World!"` | Text to display (ASCII only) |
| `width` | integer | `800` | Image width in pixels |
| `height` | integer | `1000` | Image height in pixels (4:5 ratio) |

## Features

- **Text Cleaning**: Automatically removes emojis and non-ASCII characters
- **Anti-aliasing**: 2x supersampling for crisp text rendering
- **Gradient Background**: Subtle fade from dark gray (30,30,30) to black (0,0,0)
- **Smart Font Loading**: Falls back gracefully if fonts are unavailable
- **Health Check**: `/health` endpoint for monitoring

## Common Dimensions

| Platform | Ratio | Dimensions | Usage |
|----------|-------|------------|-------|
| Instagram Post | 1:1 | 1080×1080 | Square posts |
| Instagram Story | 9:16 | 1080×1920 | Vertical stories |
| Twitter/X Card | 16:9 | 1200×675 | Link previews |
| Facebook Post | 1.91:1 | 1200×630 | Shared links |
| Default | 4:5 | 800×1000 | General use |

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Pillow** - Image processing library
- **Uvicorn** - ASGI server
- **Docker** - Containerization
- **Manrope** - Beautiful sans-serif font

## Project Structure

```
.
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Deployment configuration
├── main.py                 # FastAPI application
├── pyproject.toml          # Python dependencies
└── fonts/                  # Font files
    ├── Manrope-Bold.ttf
    └── Manrope-Variable.ttf
```

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "message": "Text to Image Generator API"
}
```

## Deployment

### Dokploy

1. Push to Git repository
2. Create new app in Dokploy
3. Connect repository
4. Deploy automatically

### Self-Hosted

```bash
# Clone the repository
git clone <your-repo>
cd wandering-waterfall-e545

# Deploy with Docker Compose
docker-compose up -d
```

## Configuration

Environment variables (optional):

- `PORT` - Server port (default: 8000)
- `WORKERS` - Number of worker processes (default: 4)

## License

Private

## Support

For issues and questions, please open an issue in the repository.

