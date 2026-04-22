"""Utilities for archiving Twilio recordings to MinIO."""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

import requests
from minio import Minio
from minio.error import S3Error

from app.twilio.config import (
	MINIO_ACCESS_KEY,
	MINIO_BUCKET,
	MINIO_ENDPOINT,
	MINIO_PUBLIC_BASE_URL,
	MINIO_SECRET_KEY,
	TWILIO_ACCOUNT_SID,
	TWILIO_AUTH_TOKEN,
)

logger = logging.getLogger(__name__)


def _normalize_endpoint(endpoint: str) -> Tuple[str, bool]:
	value = (endpoint or "").strip()
	if value.startswith("http://"):
		return value[len("http://") :], False
	if value.startswith("https://"):
		return value[len("https://") :], True
	return value, False


def _public_recording_base(host: str, secure: bool) -> str:
	base = (MINIO_PUBLIC_BASE_URL or "").strip().rstrip("/")
	if base:
		return base
	scheme = "https" if secure else "http"
	return f"{scheme}://{host}"


def _twilio_media_url(recording_url: str) -> str:
	# Twilio often sends RecordingUrl without an extension; append .mp3 for direct media.
	if not recording_url:
		return recording_url
	trimmed = recording_url.strip()
	if "." in trimmed.rsplit("/", 1)[-1]:
		return trimmed
	return f"{trimmed}.mp3"


def _twilio_recording_filename(recording_url: str, recording_sid: Optional[str], response_id: str) -> str:
	media_url = _twilio_media_url(recording_url)
	parsed = urlparse(media_url)
	filename = PurePosixPath(parsed.path).name
	if filename:
		return filename
	identifier = recording_sid or response_id or uuid.uuid4().hex
	return f"{identifier}.mp3"


def _get_minio_client() -> Optional[Tuple[Minio, str, bool]]:
	if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY and MINIO_BUCKET):
		return None

	host, secure = _normalize_endpoint(MINIO_ENDPOINT)
	if not host:
		return None

	client = Minio(
		host,
		access_key=MINIO_ACCESS_KEY,
		secret_key=MINIO_SECRET_KEY,
		secure=secure,
	)
	return client, host, secure


def _parse_stored_minio_url(minio_url: str) -> Tuple[Optional[str], Optional[str]]:
	"""Extract bucket and object name from a stored MinIO URL."""
	if not minio_url:
		return None, None

	parsed = urlparse(minio_url)
	path = (parsed.path or "").lstrip("/")
	if not path:
		return None, None

	# Handle MinIO console-style links: /browser/<bucket>/<urlencoded-object>
	if path.startswith("browser/"):
		parts = path.split("/", 2)
		if len(parts) < 3:
			return None, None
		bucket = parts[1]
		object_name = unquote(parts[2])
		return bucket, object_name

	parts = path.split("/", 1)
	if len(parts) < 2:
		return None, None
	return parts[0], parts[1]


def recording_playback_url(
	minio_url: Optional[str],
	twilio_url: Optional[str],
	expires_seconds: int = 3600,
) -> Optional[str]:
	"""Return a browser-playable recording URL.

	Preference order:
	1) Presigned MinIO URL when possible.
	2) Stored MinIO URL as-is.
	3) Twilio media URL fallback.
	"""
	if minio_url:
		bundle = _get_minio_client()
		bucket, object_name = _parse_stored_minio_url(minio_url)
		if bundle and bucket and object_name:
			client, _, _ = bundle
			try:
				return client.presigned_get_object(
					bucket_name=bucket,
					object_name=object_name,
					expires=timedelta(seconds=expires_seconds),
				)
			except S3Error as exc:
				logger.warning("Failed to generate presigned MinIO URL: %s", exc)
		return minio_url

	if twilio_url:
		return _twilio_media_url(twilio_url)

	return None


def archive_twilio_recording(
	recording_url: str,
	call_sid: str,
	question_index: int,
	recording_sid: Optional[str],
	response_id: str,
) -> Optional[str]:
	"""Download a recording from Twilio and upload it to MinIO.

	Returns a MinIO object URL when successful, otherwise None.
	"""
	minio_bundle = _get_minio_client()
	if not minio_bundle:
		return None

	client, host, secure = minio_bundle
	media_url = _twilio_media_url(recording_url)

	try:
		media_resp = requests.get(
			media_url,
			auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
			timeout=30,
		)
		media_resp.raise_for_status()
		content = media_resp.content
		if not content:
			logger.warning("Twilio recording fetch returned empty body: %s", media_url)
			return None

		if not client.bucket_exists(MINIO_BUCKET):
			client.make_bucket(MINIO_BUCKET)

		today = datetime.now(timezone.utc)
		filename = _twilio_recording_filename(recording_url, recording_sid, response_id)
		object_name = (
			f"twilio/{today:%Y/%m/%d}/"
			f"{call_sid}/{filename}"
		)

		content_type = media_resp.headers.get("Content-Type", "audio/mpeg")
		client.put_object(
			MINIO_BUCKET,
			object_name,
			data=io.BytesIO(content),
			length=len(content),
			content_type=content_type,
		)

		base = _public_recording_base(host, secure)
		return f"{base}/{MINIO_BUCKET}/{object_name}"

	except (requests.RequestException, S3Error, ValueError) as exc:
		logger.warning("Failed to archive Twilio recording to MinIO: %s", exc)
		return None
