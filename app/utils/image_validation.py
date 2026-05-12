import struct
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURES = (b"\xff\xd8\xff",)
GIF_SIGNATURES = (b"GIF87a", b"GIF89a")


def validate_image_bytes(content: bytes, mime_type: str) -> None:
    if not content:
        raise ValueError("Image payload is empty")

    match mime_type:
        case "image/png":
            _validate_png(content)
        case "image/jpeg":
            _validate_jpeg(content)
        case "image/gif":
            _validate_gif(content)
        case "image/webp":
            _validate_webp(content)
        case _:
            raise ValueError(f"Unsupported image MIME type: {mime_type}")


def _validate_png(content: bytes) -> None:
    if not content.startswith(PNG_SIGNATURE):
        raise ValueError("Invalid PNG signature")

    offset = len(PNG_SIGNATURE)
    seen_ihdr = False
    seen_iend = False

    while offset < len(content):
        if offset + 12 > len(content):
            raise ValueError("Truncated PNG chunk header")

        length = struct.unpack(">I", content[offset : offset + 4])[0]
        chunk_type = content[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4

        if crc_end > len(content):
            raise ValueError(f"Truncated PNG chunk: {chunk_type.decode('ascii', errors='replace')}")

        expected_crc = struct.unpack(">I", content[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + content[data_start:data_end]) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            chunk_name = chunk_type.decode("ascii", errors="replace")
            raise ValueError(f"Invalid PNG CRC for {chunk_name}: expected {expected_crc:#x}, got {actual_crc:#x}")

        if chunk_type == b"IHDR":
            seen_ihdr = True
        elif chunk_type == b"IEND":
            seen_iend = True
            if crc_end != len(content):
                raise ValueError("Unexpected trailing bytes after PNG IEND")
            break

        offset = crc_end

    if not seen_ihdr:
        raise ValueError("PNG missing IHDR chunk")
    if not seen_iend:
        raise ValueError("PNG missing IEND chunk")


def _validate_jpeg(content: bytes) -> None:
    if not content.startswith(JPEG_SIGNATURES) or not content.endswith(b"\xff\xd9"):
        raise ValueError("Invalid JPEG payload")


def _validate_gif(content: bytes) -> None:
    if not content.startswith(GIF_SIGNATURES):
        raise ValueError("Invalid GIF signature")


def _validate_webp(content: bytes) -> None:
    if len(content) < 12 or content[:4] != b"RIFF" or content[8:12] != b"WEBP":
        raise ValueError("Invalid WebP RIFF signature")
