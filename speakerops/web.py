from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from speakerops.network import NetworkPolicy, NetworkPolicyViolation


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    summary: str


class WebSearchClient:
    def search(self, query: str) -> list[SearchResult]:
        raise NotImplementedError


class DuckDuckGoSearchClient(WebSearchClient):
    def __init__(self, network_policy: NetworkPolicy | None = None):
        self.network_policy = network_policy

    def search(self, query: str) -> list[SearchResult]:
        url = "https://api.duckduckgo.com/"
        if self.network_policy:
            self.network_policy.check_url(url)
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            return fallback_results(query)

        results: list[SearchResult] = []
        abstract = data.get("AbstractText")
        abstract_url = data.get("AbstractURL")
        heading = data.get("Heading") or query
        if isinstance(abstract, str) and abstract and isinstance(abstract_url, str):
            results.append(SearchResult(title=str(heading), url=abstract_url, summary=abstract))

        for item in _flatten_related(data.get("RelatedTopics", [])):
            text = item.get("Text")
            url = item.get("FirstURL")
            if isinstance(text, str) and isinstance(url, str):
                results.append(SearchResult(title=text.split(" - ")[0][:100], url=url, summary=text))
            if len(results) >= 6:
                break

        return results or fallback_results(query)


def denied_results(query: str, exc: NetworkPolicyViolation) -> list[SearchResult]:
    return [
        SearchResult(
            title="Network request denied by policy",
            url="",
            summary=f"{exc} Research for '{query}' used the local fallback references instead.",
        ),
        *fallback_results(query),
    ]


def _flatten_related(items: list[Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("Topics"), list):
            flattened.extend(_flatten_related(item["Topics"]))
        elif isinstance(item, dict):
            flattened.append(item)
    return flattened


def fallback_results(query: str) -> list[SearchResult]:
    return [
        SearchResult(
            title="OWASP Top 10 for Large Language Model Applications",
            url="https://owasp.org/www-project-top-10-for-large-language-model-applications/",
            summary=f"Reference for common LLM application risks relevant to {query}, including prompt injection, excessive agency, and insecure output handling.",
        ),
        SearchResult(
            title="NIST AI Risk Management Framework",
            url="https://www.nist.gov/itl/ai-risk-management-framework",
            summary="Risk-management framing for trustworthy AI systems, useful for explaining governance and measurement.",
        ),
        SearchResult(
            title="Microsoft Zero Trust guidance",
            url="https://www.microsoft.com/security/business/zero-trust",
            summary="Practical control framing for identity, device, application, data, infrastructure, and network boundaries.",
        ),
    ]


def format_results(results: list[SearchResult]) -> str:
    return "\n\n".join(f"- **{result.title}**\n  URL: {result.url}\n  Summary: {result.summary}" for result in results)
