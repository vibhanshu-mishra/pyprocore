"""Email parsing utilities for future Procore automation workflows."""

from __future__ import annotations

from email import policy
from email.message import Message
from email.parser import BytesParser, Parser
from pathlib import Path

from pydantic import BaseModel, Field


class ParsedEmailAttachment(BaseModel):
    """Metadata for an attachment found in an email message."""

    filename: str
    content_type: str
    size_bytes: int = Field(ge=0)


class ParsedEmail(BaseModel):
    """Structured representation of an email message."""

    subject: str | None = None
    sender: str | None = None
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    date: str | None = None
    text_body: str | None = None
    html_body: str | None = None
    attachments: list[ParsedEmailAttachment] = Field(default_factory=list)


class EmailParser:
    """Parse raw email messages into structured data."""

    def parse_file(self, path: Path | str) -> ParsedEmail:
        """Parse an email message from a file path.

        Args:
            path: Path to a raw ``.eml`` style email file.

        Returns:
            Parsed email data.
        """
        message_path = Path(path)
        with message_path.open("rb") as file_handle:
            message = BytesParser(policy=policy.default).parse(file_handle)
        return self.parse_message(message)

    def parse_text(self, raw_email: str) -> ParsedEmail:
        """Parse an email message from raw text."""
        message = Parser(policy=policy.default).parsestr(raw_email)
        return self.parse_message(message)

    def parse_bytes(self, raw_email: bytes) -> ParsedEmail:
        """Parse an email message from raw bytes."""
        message = BytesParser(policy=policy.default).parsebytes(raw_email)
        return self.parse_message(message)

    def parse_message(self, message: Message) -> ParsedEmail:
        """Parse an ``email.message.Message`` object."""
        text_body, html_body = self._extract_bodies(message)
        return ParsedEmail(
            subject=self._header_value(message, "subject"),
            sender=self._header_value(message, "from"),
            recipients=self._split_addresses(message.get_all("to", [])),
            cc=self._split_addresses(message.get_all("cc", [])),
            date=self._header_value(message, "date"),
            text_body=text_body,
            html_body=html_body,
            attachments=self._extract_attachments(message),
        )

    @staticmethod
    def _extract_bodies(message: Message) -> tuple[str | None, str | None]:
        """Extract plain text and HTML body content from a message."""
        text_body: str | None = None
        html_body: str | None = None

        if message.is_multipart():
            for part in message.walk():
                if part.is_multipart() or part.get_content_disposition() == "attachment":
                    continue

                content_type = part.get_content_type()
                payload = EmailParser._part_text(part)
                if content_type == "text/plain" and text_body is None:
                    text_body = payload
                elif content_type == "text/html" and html_body is None:
                    html_body = payload
        else:
            payload = EmailParser._part_text(message)
            if message.get_content_type() == "text/html":
                html_body = payload
            else:
                text_body = payload

        return text_body, html_body

    @staticmethod
    def _extract_attachments(message: Message) -> list[ParsedEmailAttachment]:
        """Return attachment metadata without writing files to disk."""
        attachments: list[ParsedEmailAttachment] = []
        for part in message.walk():
            if part.get_content_disposition() != "attachment":
                continue

            filename = part.get_filename()
            if not filename:
                filename = "attachment"

            payload = part.get_payload(decode=True) or b""
            attachments.append(
                ParsedEmailAttachment(
                    filename=Path(filename).name,
                    content_type=part.get_content_type(),
                    size_bytes=len(payload),
                )
            )

        return attachments

    @staticmethod
    def _part_text(part: Message) -> str | None:
        """Decode a message part into text when possible."""
        if hasattr(part, "get_content"):
            content = part.get_content()
            return content if isinstance(content, str) else None

        payload = part.get_payload(decode=True)
        if payload is None:
            return None

        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace") if isinstance(payload, bytes) else None

    @staticmethod
    def _header_value(message: Message, name: str) -> str | None:
        """Return a header as a string when present."""
        value = message.get(name)
        return str(value) if value is not None else None

    @staticmethod
    def _split_addresses(values: list[str]) -> list[str]:
        """Split comma-separated address headers into normalized strings."""
        addresses: list[str] = []
        for value in values:
            addresses.extend(part.strip() for part in str(value).split(",") if part.strip())
        return addresses


def parse_email_file(path: Path | str) -> ParsedEmail:
    """Parse an email message from a file path."""
    return EmailParser().parse_file(path)


def parse_email_text(raw_email: str) -> ParsedEmail:
    """Parse an email message from raw text."""
    return EmailParser().parse_text(raw_email)
