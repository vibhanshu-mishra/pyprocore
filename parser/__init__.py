"""Parser utilities for Procore automation workflows."""

from parser.email_parser import (
    EmailParser,
    ParsedEmail,
    ParsedEmailAttachment,
    parse_email_file,
    parse_email_text,
)

__all__ = [
    "EmailParser",
    "ParsedEmail",
    "ParsedEmailAttachment",
    "parse_email_file",
    "parse_email_text",
]
