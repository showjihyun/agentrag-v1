"""
API Response Compression Optimization

Provides intelligent compression for API responses:
- Content-type aware compression
- Size-based compression decisions
- Multiple compression algorithms (gzip, brotli)
- Streaming compression support
"""

import gzip
import io
import logging
from typing import Any, Callable, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# Try to import brotli (optional)
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.info("Brotli not available, using gzip only")


class CompressionAlgorithm(str, Enum):
    """Supported compression algorithms."""
    GZIP = "gzip"
    BROTLI = "br"
    NONE = "identity"


@dataclass
class CompressionConfig:
    """Compression configuration."""
    
    # Minimum size to compress (bytes)
    min_size: int = 500
    
    # Maximum size to compress (bytes) - very large responses may be better uncompressed
    max_size: int = 10 * 1024 * 1024  # 10MB
    
    # Compression level (1-9 for gzip, 0-11 for brotli)
    gzip_level: int = 6
    brotli_level: int = 4
    
    # Content types to compress
    compressible_types: Set[str] = None
    
    # Paths to skip compression
    skip_paths: Set[str] = None
    
    def __post_init__(self):
        if self.compressible_types is None:
            self.compressible_types = {
                "application/json",
                "application/xml",
                "text/html",
                "text/plain",
                "text/css",
                "text/javascript",
                "application/javascript",
                "image/svg+xml",
            }
        
        if self.skip_paths is None:
            self.skip_paths = {
                "/health",
                "/health/live",
                "/health/ready",
                "/api/v1/health/live",
                "/api/v1/health/ready",
            }


def get_preferred_encoding(accept_encoding: str) -> CompressionAlgorithm:
    """
    Determine the best compression algorithm based on Accept-Encoding header.
    
    Preference order: brotli > gzip > none
    """
    if not accept_encoding:
        return CompressionAlgorithm.NONE
    
    accept_encoding = accept_encoding.lower()
    
    # Prefer brotli if available and accepted
    if BROTLI_AVAILABLE and "br" in accept_encoding:
        return CompressionAlgorithm.BROTLI
    
    if "gzip" in accept_encoding:
        return CompressionAlgorithm.GZIP
    
    return CompressionAlgorithm.NONE


def compress_gzip(data: bytes, level: int = 6) -> bytes:
    """Compress data using gzip."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=level) as f:
        f.write(data)
    return buffer.getvalue()


def compress_brotli(data: bytes, level: int = 4) -> bytes:
    """Compress data using brotli."""
    if not BROTLI_AVAILABLE:
        raise RuntimeError("Brotli not available")
    return brotli.compress(data, quality=level)


def compress_data(
    data: bytes,
    algorithm: CompressionAlgorithm,
    config: CompressionConfig,
) -> tuple[bytes, bool]:
    """
    Compress data using specified algorithm.
    
    Returns:
        Tuple of (compressed_data, was_compressed)
    """
    if algorithm == CompressionAlgorithm.NONE:
        return data, False
    
    # Check size limits
    if len(data) < config.min_size:
        return data, False
    
    if len(data) > config.max_size:
        logger.debug(f"Skipping compression for large response ({len(data)} bytes)")
        return data, False
    
    try:
        if algorithm == CompressionAlgorithm.GZIP:
            compressed = compress_gzip(data, config.gzip_level)
        elif algorithm == CompressionAlgorithm.BROTLI:
            compressed = compress_brotli(data, config.brotli_level)
        else:
            return data, False
        
        # Only use compressed if it's actually smaller
        if len(compressed) < len(data):
            compression_ratio = (1 - len(compressed) / len(data)) * 100
            logger.debug(
                f"Compressed {len(data)} -> {len(compressed)} bytes "
                f"({compression_ratio:.1f}% reduction) using {algorithm.value}"
            )
            return compressed, True
        else:
            logger.debug(
                f"Compression not beneficial ({len(data)} -> {len(compressed)} bytes)"
            )
            return data, False
            
    except Exception as e:
        logger.warning(f"Compression failed: {e}")
        return data, False


def should_compress(
    content_type: Optional[str],
    path: str,
    config: CompressionConfig,
) -> bool:
    """Determine if response should be compressed."""
    # Skip certain paths
    if path in config.skip_paths:
        return False
    
    # Check content type
    if not content_type:
        return False
    
    # Extract base content type (without charset, etc.)
    base_type = content_type.split(";")[0].strip().lower()
    
    return base_type in config.compressible_types


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for intelligent response compression.
    
    Features:
    - Content-type aware compression
    - Size-based decisions
    - Multiple algorithm support
    - Proper header handling
    """
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[CompressionConfig] = None,
    ):
        super().__init__(app)
        self.config = config or CompressionConfig()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and optionally compress response."""
        # Get accepted encodings
        accept_encoding = request.headers.get("accept-encoding", "")
        algorithm = get_preferred_encoding(accept_encoding)
        
        # Process request
        response = await call_next(request)
        
        # Skip if no compression or streaming response
        if algorithm == CompressionAlgorithm.NONE:
            return response
        
        if isinstance(response, StreamingResponse):
            # Don't compress streaming responses
            return response
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return response
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not should_compress(content_type, request.url.path, self.config):
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Compress
        compressed_body, was_compressed = compress_data(body, algorithm, self.config)
        
        if was_compressed:
            # Create new response with compressed body
            headers = dict(response.headers)
            headers["content-encoding"] = algorithm.value
            headers["content-length"] = str(len(compressed_body))
            headers["vary"] = "Accept-Encoding"
            
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )
        
        # Return original response
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


# ============================================================================
# Large Response Handling
# ============================================================================

async def compress_large_response(
    data: Any,
    request: Request,
    config: Optional[CompressionConfig] = None,
) -> Response:
    """
    Compress a large response with proper headers.
    
    Usage:
        @router.get("/large-data")
        async def get_large_data(request: Request):
            data = await fetch_large_data()
            return await compress_large_response(data, request)
    """
    import json
    
    config = config or CompressionConfig()
    
    # Serialize data
    if isinstance(data, (dict, list)):
        body = json.dumps(data).encode("utf-8")
        content_type = "application/json"
    elif isinstance(data, str):
        body = data.encode("utf-8")
        content_type = "text/plain"
    elif isinstance(data, bytes):
        body = data
        content_type = "application/octet-stream"
    else:
        body = str(data).encode("utf-8")
        content_type = "text/plain"
    
    # Get preferred encoding
    accept_encoding = request.headers.get("accept-encoding", "")
    algorithm = get_preferred_encoding(accept_encoding)
    
    # Compress
    compressed_body, was_compressed = compress_data(body, algorithm, config)
    
    headers = {
        "content-type": content_type,
        "content-length": str(len(compressed_body)),
    }
    
    if was_compressed:
        headers["content-encoding"] = algorithm.value
        headers["vary"] = "Accept-Encoding"
    
    return Response(
        content=compressed_body,
        headers=headers,
    )


# ============================================================================
# Streaming Compression
# ============================================================================

async def compress_stream(
    data_generator,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    chunk_size: int = 8192,
):
    """
    Generator for streaming compressed data.
    
    Usage:
        @router.get("/stream")
        async def stream_data(request: Request):
            async def generate():
                for chunk in large_data_source():
                    yield chunk
            
            return StreamingResponse(
                compress_stream(generate()),
                media_type="application/octet-stream",
                headers={"content-encoding": "gzip"}
            )
    """
    if algorithm == CompressionAlgorithm.GZIP:
        compressor = gzip.compressobj(level=6)
        
        async for chunk in data_generator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            
            compressed = compressor.compress(chunk)
            if compressed:
                yield compressed
        
        # Flush remaining data
        yield compressor.flush()
        
    elif algorithm == CompressionAlgorithm.BROTLI and BROTLI_AVAILABLE:
        compressor = brotli.Compressor(quality=4)
        
        async for chunk in data_generator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            
            compressed = compressor.process(chunk)
            if compressed:
                yield compressed
        
        # Flush remaining data
        yield compressor.finish()
        
    else:
        # No compression
        async for chunk in data_generator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            yield chunk


def setup_compression(
    app,
    min_size: int = 500,
    gzip_level: int = 6,
) -> None:
    """
    Setup compression middleware for the application.
    
    Usage:
        from backend.core.compression import setup_compression
        
        app = FastAPI()
        setup_compression(app, min_size=1000)
    """
    config = CompressionConfig(
        min_size=min_size,
        gzip_level=gzip_level,
    )
    
    app.add_middleware(CompressionMiddleware, config=config)
    logger.info(
        f"Compression middleware configured "
        f"(min_size={min_size}, gzip_level={gzip_level}, "
        f"brotli={'available' if BROTLI_AVAILABLE else 'not available'})"
    )
