"""
Resume file storage helper.

Local filesystem storage for the MVP (see docs/resume-module.md for
the planned S3/Azure migration path). Deliberately kept as a small set
of functions rather than a storage-abstraction class hierarchy — "keep
it simple but clean enough to replace later," not a full abstraction
built ahead of actual need. A future cloud-storage swap would replace
the bodies of `save_upload`/`delete_file`/`open_file` without touching
their signatures or any caller.

Two independent validation layers, both required to pass (neither
alone is trustworthy):
- Extension + declared `Content-Type` — cheap, but trivially spoofable
  by renaming a file or lying about its MIME type.
- Magic-byte file signature — sniffs the file's actual leading bytes,
  so a renamed `.exe` claiming to be a PDF is still rejected. No new
  dependency (e.g. `python-magic`/libmagic) was introduced for this —
  the three MVP formats have short, well-known, easy-to-check
  signatures, so a hand-rolled check keeps this genuinely simple
  rather than pulling in a system-level library for three constants.

Size is enforced by streaming: the upload is read in fixed-size chunks
and the running total is checked against the limit as it goes, so an
oversized file is rejected before it's ever fully written to disk —
never by trusting a client-supplied size/Content-Length.
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError

logger = logging.getLogger("app")

# Project root: this file lives at app/modules/resumes/storage.py, so
# three parents up is the project root (the same directory containing
# requirements.txt, alembic/, etc.).
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_READ_CHUNK_SIZE = 1024 * 1024  # 1 MB per chunk while streaming to disk

_ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}
# Permissive fallbacks some browsers/OSes send instead of the "correct"
# type — accepted so legitimate uploads aren't rejected on a client
# quirk; the magic-byte check below is the real gate either way.
_PERMISSIVE_CONTENT_TYPES = {"application/octet-stream", ""}

_MAGIC_SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),  # legacy OLE/CFBF container
    ".docx": (b"PK\x03\x04",),  # DOCX is a ZIP archive
}


@dataclass(frozen=True)
class SavedFile:
    file_name: str  # original filename, as supplied by the client
    file_path: str  # path relative to the upload root — never exposed to clients
    file_type: str  # declared content type, as validated
    file_size: int  # bytes actually written


def _get_upload_root() -> Path:
    """
    Resolved fresh on every call (not cached at import time) so tests
    can point `settings.RESUME_UPLOAD_DIR` at a temporary directory via
    monkeypatch without any production code path changing.
    """
    return _PROJECT_ROOT / settings.RESUME_UPLOAD_DIR


def _max_file_size_bytes() -> int:
    return settings.RESUME_MAX_FILE_SIZE_MB * 1024 * 1024


def _validate_extension_and_content_type(original_filename: str, content_type: Optional[str]) -> str:
    """Returns the validated, lowercased extension (e.g. '.pdf') or raises ValidationError."""
    extension = Path(original_filename).suffix.lower()
    if extension not in _ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            "Unsupported file type. Only PDF, DOC, and DOCX files are allowed.",
            error_code="UNSUPPORTED_FILE_TYPE",
        )

    declared = (content_type or "").lower()
    allowed_for_extension = _ALLOWED_CONTENT_TYPES[extension]
    if declared not in allowed_for_extension and declared not in _PERMISSIVE_CONTENT_TYPES:
        raise ValidationError(
            "The declared file content type does not match the file extension.",
            error_code="CONTENT_TYPE_MISMATCH",
        )

    return extension


def _validate_signature(extension: str, header_bytes: bytes) -> None:
    """Sniff the file's actual leading bytes against the expected signature for its extension."""
    signatures = _MAGIC_SIGNATURES[extension]
    if not any(header_bytes.startswith(sig) for sig in signatures):
        raise ValidationError(
            "The file's content does not match its extension.",
            error_code="FILE_CONTENT_MISMATCH",
        )


async def save_upload(student_id: int, upload: UploadFile) -> SavedFile:
    """
    Validate and stream an uploaded file to disk under a generated,
    unguessable filename — the original filename is never trusted as
    a physical path component (see module docstring).

    Raises `ValidationError` (422) for any invalid extension, content
    type, signature, or oversized file. On any failure after a partial
    write has started, the partial file is removed before raising.
    """
    original_filename = upload.filename or "upload"
    extension = _validate_extension_and_content_type(original_filename, upload.content_type)

    student_dir = _get_upload_root() / str(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)

    generated_name = f"{uuid.uuid4().hex}{extension}"
    destination = student_dir / generated_name

    max_bytes = _max_file_size_bytes()
    bytes_written = 0
    signature_checked = False

    try:
        with open(destination, "wb") as out_file:
            while True:
                chunk = await upload.read(_READ_CHUNK_SIZE)
                if not chunk:
                    break

                if not signature_checked:
                    _validate_signature(extension, chunk)
                    signature_checked = True

                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise ValidationError(
                        f"File exceeds the maximum allowed size of "
                        f"{settings.RESUME_MAX_FILE_SIZE_MB} MB.",
                        error_code="FILE_TOO_LARGE",
                    )

                out_file.write(chunk)

        if bytes_written == 0:
            raise ValidationError("The uploaded file is empty.", error_code="EMPTY_FILE")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    relative_path = str(destination.relative_to(_get_upload_root()))
    return SavedFile(
        file_name=original_filename,
        file_path=relative_path,
        file_type=upload.content_type or _ALLOWED_CONTENT_TYPES[extension].copy().pop(),
        file_size=bytes_written,
    )


def resolve_absolute_path(relative_path: str) -> Optional[Path]:
    """
    Resolve a stored relative path to an absolute filesystem path,
    verifying it stays within the upload root (defense in depth — the
    stored path is always one this module generated itself via
    `save_upload`, never client input, but this guard costs nothing
    and protects against any future code path that might not hold
    that invariant). Returns None if the resolved path would escape
    the upload root, or if the file doesn't actually exist on disk.
    """
    upload_root = _get_upload_root().resolve()
    candidate = (upload_root / relative_path).resolve()

    try:
        candidate.relative_to(upload_root)
    except ValueError:
        logger.error("Resume file path escaped upload root: %r", relative_path)
        return None

    if not candidate.is_file():
        return None
    return candidate


def delete_file(relative_path: Optional[str]) -> None:
    """
    Delete a previously-saved file. Silently no-ops if `relative_path`
    is None or the file is already missing on disk — a physical file
    missing despite DB metadata referencing it is treated as "nothing
    to clean up," not an error (see docs/resume-module.md).
    """
    if relative_path is None:
        return

    absolute_path = resolve_absolute_path(relative_path)
    if absolute_path is None:
        return

    try:
        absolute_path.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - defensive; unexpected filesystem error
        logger.error("Failed to delete resume file %r", relative_path, exc_info=True)
