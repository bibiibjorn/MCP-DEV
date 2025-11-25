"""
Mermaid diagram renderer for MCP image content.
Converts Mermaid code to PNG images using mermaid.ink API.
"""

import base64
import logging
import zlib
from typing import Optional, Dict, Any, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Cache for rendered diagrams to avoid repeated API calls
_render_cache: Dict[int, bytes] = {}
_CACHE_MAX_SIZE = 50


def _encode_mermaid_for_ink(mermaid_code: str) -> str:
    """
    Encode Mermaid code for mermaid.ink URL using pako deflate + base64.

    mermaid.ink uses a specific encoding:
    1. UTF-8 encode the Mermaid code
    2. Compress with zlib (deflate, raw)
    3. Base64 encode
    4. Make URL-safe (replace +/ with -_)
    """
    # Compress with zlib (raw deflate, no header)
    compressed = zlib.compress(mermaid_code.encode('utf-8'), level=9)[2:-4]  # Strip zlib header/trailer

    # Base64 encode and make URL-safe
    b64 = base64.b64encode(compressed).decode('ascii')
    url_safe = b64.replace('+', '-').replace('/', '_')

    return url_safe


def _encode_mermaid_simple(mermaid_code: str) -> str:
    """
    Simple base64 encoding for mermaid.ink (fallback method).
    """
    return base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('ascii')


# Maximum URL length for mermaid.ink API (HTTP 414 occurs around 8KB)
MAX_URL_LENGTH = 7500


def render_mermaid_to_png(
    mermaid_code: str,
    theme: str = "default",
    background_color: str = "white",
    width: Optional[int] = None,
    use_cache: bool = True
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Render Mermaid diagram to PNG using mermaid.ink API.

    Args:
        mermaid_code: The Mermaid diagram code
        theme: Mermaid theme (default, dark, forest, neutral)
        background_color: Background color (white, transparent)
        width: Optional width in pixels
        use_cache: Whether to use caching (default: True)

    Returns:
        Tuple of (png_bytes, error_message)
        - On success: (bytes, None)
        - On failure: (None, error_string)
    """
    try:
        import httpx
    except ImportError:
        return None, "httpx library not installed. Run: pip install httpx"

    # Check cache
    cache_key = hash((mermaid_code, theme, background_color, width))
    if use_cache and cache_key in _render_cache:
        logger.debug("Mermaid render cache hit")
        return _render_cache[cache_key], None

    try:
        # Use simple base64 encoding (more reliable)
        encoded = _encode_mermaid_simple(mermaid_code)

        # Build URL with options
        # mermaid.ink format: https://mermaid.ink/img/{base64}?type=png&theme=...
        url = f"https://mermaid.ink/img/{encoded}"

        # Check URL length - mermaid.ink returns HTTP 414 if URL is too long
        if len(url) > MAX_URL_LENGTH:
            logger.warning(f"Mermaid URL too long ({len(url)} chars > {MAX_URL_LENGTH} limit)")
            return None, f"DIAGRAM_TOO_LARGE: URL length {len(url)} exceeds limit. Use HTML fallback."

        params = {"type": "png"}
        if theme != "default":
            params["theme"] = theme
        if background_color != "white":
            params["bgColor"] = background_color
        if width:
            params["width"] = str(width)

        # Make request with timeout
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

            png_data = response.content

            # Validate it's actually a PNG
            if not png_data.startswith(b'\x89PNG'):
                logger.warning("mermaid.ink returned non-PNG data")
                return None, "Invalid response from mermaid.ink (not PNG data)"

            # Cache the result
            if use_cache:
                if len(_render_cache) >= _CACHE_MAX_SIZE:
                    # Simple LRU: remove oldest entry
                    _render_cache.pop(next(iter(_render_cache)))
                _render_cache[cache_key] = png_data

            logger.debug(f"Rendered Mermaid diagram: {len(png_data)} bytes")
            return png_data, None

    except httpx.TimeoutException:
        return None, "Timeout rendering Mermaid diagram (mermaid.ink)"
    except httpx.HTTPStatusError as e:
        return None, f"HTTP error from mermaid.ink: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error rendering Mermaid diagram: {e}")
        return None, f"Failed to render Mermaid diagram: {str(e)}"


def render_mermaid_to_svg(
    mermaid_code: str,
    theme: str = "default",
    background_color: str = "white"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Render Mermaid diagram to SVG using mermaid.ink API.

    Args:
        mermaid_code: The Mermaid diagram code
        theme: Mermaid theme (default, dark, forest, neutral)
        background_color: Background color

    Returns:
        Tuple of (svg_string, error_message)
    """
    try:
        import httpx
    except ImportError:
        return None, "httpx library not installed. Run: pip install httpx"

    try:
        encoded = _encode_mermaid_simple(mermaid_code)
        url = f"https://mermaid.ink/svg/{encoded}"

        params = {}
        if theme != "default":
            params["theme"] = theme
        if background_color != "white":
            params["bgColor"] = background_color

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text, None

    except Exception as e:
        return None, f"Failed to render SVG: {str(e)}"


def get_mermaid_image_content(
    mermaid_code: str,
    theme: str = "default",
    max_size_bytes: int = 900000  # Under 1MB limit for Claude Desktop
) -> Dict[str, Any]:
    """
    Get Mermaid diagram as MCP ImageContent dict.
    Ensures image is under Claude Desktop's 1MB limit.

    Args:
        mermaid_code: The Mermaid diagram code
        theme: Mermaid theme
        max_size_bytes: Maximum image size (default 900KB to be safe under 1MB)

    Returns:
        Dict suitable for MCP ImageContent, or error dict
    """
    png_data, error = render_mermaid_to_png(mermaid_code, theme=theme)

    if error:
        return {
            "success": False,
            "error": error,
            "mermaid_code": mermaid_code
        }

    # Check size and log it
    size_kb = len(png_data) / 1024
    logger.info(f"Mermaid PNG size: {size_kb:.1f} KB")

    # If too large, return error (Claude Desktop has 1MB limit)
    if len(png_data) > max_size_bytes:
        logger.warning(f"Mermaid image too large ({size_kb:.1f} KB > {max_size_bytes/1024:.0f} KB limit)")
        return {
            "success": False,
            "error": f"Image too large ({size_kb:.0f} KB). Claude Desktop has 1MB limit.",
            "mermaid_code": mermaid_code
        }

    return {
        "success": True,
        "type": "image",
        "data": base64.b64encode(png_data).decode('ascii'),
        "mimeType": "image/png",
        "size_bytes": len(png_data)
    }


def clear_render_cache():
    """Clear the render cache."""
    _render_cache.clear()
    logger.debug("Mermaid render cache cleared")
