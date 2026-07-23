"""Deterministic local discovery routing over capability metadata."""

from __future__ import annotations

import re
from pathlib import Path

from pyprocore.catalog import CatalogEndpoint, CatalogEndpointSafety, load_oas_catalog
from pyprocore.discovery.models import (
    DiscoveryCapability,
    DiscoveryQuery,
    DiscoveryRouteCandidate,
    DiscoveryRouteResult,
)
from pyprocore.discovery.registry import list_discovery_capabilities

STOPWORDS = {
    "a",
    "an",
    "and",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def search_discovery_capabilities(
    text: str,
    *,
    limit: int = 10,
    capabilities: list[DiscoveryCapability] | None = None,
) -> DiscoveryRouteResult:
    """Search built-in capability metadata using deterministic lexical scoring.

    Args:
        text: User intent or search text.
        limit: Maximum number of candidates to return.
        capabilities: Optional capability list, primarily for tests.

    Returns:
        Ranked route suggestions. This function only searches local metadata.
    """
    query = DiscoveryQuery(text=text, limit=limit)
    return _rank_capabilities(
        query,
        capabilities or list_discovery_capabilities(),
    )


def route_discovery_query(text: str, *, limit: int = 5) -> DiscoveryRouteResult:
    """Return route suggestions for a user intent.

    Args:
        text: User intent.
        limit: Maximum number of candidates.

    Returns:
        Ranked metadata-only route candidates.
    """
    return search_discovery_capabilities(text, limit=limit)


def search_oas_catalog_capabilities(
    oas_path: str | Path,
    text: str,
    *,
    limit: int = 10,
) -> DiscoveryRouteResult:
    """Search local OAS endpoint metadata alongside built-in capabilities.

    Args:
        oas_path: Local OAS JSON file path.
        text: User intent or search text.
        limit: Maximum number of candidates to return.

    Returns:
        Ranked route suggestions from local metadata and local OAS endpoints.
    """
    catalog = load_oas_catalog(oas_path)
    capabilities = [
        *list_discovery_capabilities(),
        *[_capability_from_catalog_endpoint(endpoint) for endpoint in catalog.endpoints],
    ]
    query = DiscoveryQuery(text=text, limit=limit, oas_path=str(oas_path))
    return _rank_capabilities(query, capabilities)


def _rank_capabilities(
    query: DiscoveryQuery,
    capabilities: list[DiscoveryCapability],
) -> DiscoveryRouteResult:
    """Rank capabilities against a normalized query."""
    query_terms = _tokens(query.text)
    candidates: list[DiscoveryRouteCandidate] = []
    for capability in capabilities:
        score, matched_terms, reasons = _score_capability(query.text, query_terms, capability)
        if score <= 0:
            continue
        candidates.append(
            DiscoveryRouteCandidate(
                capability=capability,
                score=score,
                matched_terms=matched_terms,
                reasons=reasons,
            )
        )
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            candidate.score,
            -len(candidate.capability.name),
            candidate.capability.name,
        ),
        reverse=True,
    )
    return DiscoveryRouteResult(query=query, candidates=ranked[: max(query.limit, 0)])


def _score_capability(
    query_text: str,
    query_terms: set[str],
    capability: DiscoveryCapability,
) -> tuple[float, list[str], list[str]]:
    """Score one capability using fields users naturally search."""
    haystacks = {
        "name": capability.name,
        "title": capability.title,
        "description": capability.description,
        "resource_family": capability.resource_family,
        "operations": " ".join(capability.operations),
        "keywords": " ".join(capability.keywords),
        "examples": " ".join(capability.examples),
        "safety_labels": " ".join(capability.safety_labels),
    }
    lower_query = query_text.strip().lower()
    score = 0.0
    matched_terms: set[str] = set()
    reasons: list[str] = []
    searchable_text = " ".join(haystacks.values()).lower()

    if lower_query and lower_query in searchable_text:
        score += 8.0
        reasons.append("matched the full query phrase")

    weights = {
        "name": 5.0,
        "title": 4.0,
        "resource_family": 4.0,
        "keywords": 3.0,
        "operations": 2.0,
        "examples": 2.0,
        "description": 1.5,
        "safety_labels": 1.0,
    }
    for field, value in haystacks.items():
        value_terms = _tokens(value)
        field_matches = sorted(query_terms & value_terms)
        if not field_matches:
            continue
        score += len(field_matches) * weights[field]
        matched_terms.update(field_matches)
        reasons.append(f"matched {', '.join(field_matches)} in {field}")

    return score, sorted(matched_terms), reasons


def _capability_from_catalog_endpoint(endpoint: CatalogEndpoint) -> DiscoveryCapability:
    """Convert a local OAS endpoint row into discovery metadata."""
    safety_label = (
        "local_oas_read_only_candidate"
        if endpoint.safety == CatalogEndpointSafety.READ_ONLY
        else (
            "local_oas_risky_write_candidate"
            if endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION
            else "local_oas_unknown_candidate"
        )
    )
    operation = f"{endpoint.method} {endpoint.path}"
    title = endpoint.summary or endpoint.operation_id or operation
    keywords = [
        endpoint.method.lower(),
        endpoint.path_area.replace("_", " "),
        *_tokens(endpoint.path),
        *_tokens(endpoint.operation_id or ""),
        *_tokens(endpoint.summary or ""),
        *[tag.lower() for tag in endpoint.tags],
    ]
    capability_name = (
        f"oas:{endpoint.method.lower()}:{endpoint.path_area}:"
        f"{endpoint.operation_id or endpoint.path}"
    )
    return DiscoveryCapability(
        name=capability_name,
        title=f"OAS {title}",
        description=(
            "Local OAS endpoint metadata candidate. This entry is for discovery only "
            f"and is classified as {endpoint.safety.value}."
        ),
        resource_family=f"oas:{endpoint.path_area}",
        operations=[operation],
        keywords=sorted(set(keywords)),
        examples=[operation],
        safety_labels=[
            "metadata_only",
            "execution_disabled",
            "local_oas_only",
            "remote_oas_fetch_disabled",
            "procore_api_call_disabled",
            "write_disabled",
            safety_label,
        ],
        source="local_oas",
    )


def _tokens(text: str) -> set[str]:
    """Tokenize local metadata for deterministic lexical matching."""
    terms = {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token and token not in STOPWORDS
    }
    expanded: set[str] = set(terms)
    for term in list(terms):
        if term.endswith("s") and len(term) > 3:
            expanded.add(term[:-1])
    return expanded
