"""Pruebas unitarias para DomainFilter y SearchEngine (Fase 4)."""

import pytest
from unittest.mock import patch, MagicMock

from docscout.core.models import SearchResultItem
from docscout.discovery.domain_filter import DomainFilter
from docscout.discovery.search_engine import SearchEngine


def test_domain_filter_scoring_catalog():
    assert DomainFilter.calculate_confidence_score("https://docs.python.org/3/library/") == 1.0
    assert DomainFilter.calculate_confidence_score("https://fastapi.tiangolo.com/tutorial/") == 1.0
    assert DomainFilter.calculate_confidence_score("https://docs.docker.com/get-started/") == 1.0
    assert DomainFilter.calculate_confidence_score("https://react.dev/reference/react") == 1.0


def test_domain_filter_scoring_patterns():
    assert DomainFilter.calculate_confidence_score("https://my-tool.readthedocs.io/en/latest/") == 0.85
    assert DomainFilter.calculate_confidence_score("https://docs.awesome-framework.org/guide") == 0.85
    assert DomainFilter.calculate_confidence_score("https://cool-lib.dev/docs/getting-started") == 0.85


def test_domain_filter_deprecates_aggregators():
    assert DomainFilter.calculate_confidence_score("https://medium.com/@user/fastapi-guide") == 0.10
    assert DomainFilter.calculate_confidence_score("https://geeksforgeeks.org/python-tutorial") == 0.10
    assert DomainFilter.calculate_confidence_score("https://w3schools.com/docker/default.asp") == 0.10
    assert DomainFilter.is_spam_or_aggregator("https://dev.to/author/my-article") is True


def test_domain_filter_filter_and_rank():
    raw_results = [
        SearchResultItem(title="Medium Article", url="https://medium.com/fastapi-tip", snippet="A blog post"),
        SearchResultItem(title="Official Docs", url="https://fastapi.tiangolo.com/tutorial/", snippet="Official FastAPI guide"),
        SearchResultItem(title="ReadTheDocs Library", url="https://pydantic.readthedocs.io/en/latest/", snippet="RTD docs"),
    ]

    ranked = DomainFilter.filter_and_rank(raw_results, min_confidence=0.50)

    # El resultado de Medium debe ser descartado (< 0.50)
    assert len(ranked) == 2
    # El resultado oficial con score 1.0 debe ser el primero
    assert ranked[0].url == "https://fastapi.tiangolo.com/tutorial/"
    assert ranked[0].is_official_domain is True
    assert ranked[1].url == "https://pydantic.readthedocs.io/en/latest/"


def test_search_engine_build_search_query():
    q1 = SearchEngine.build_search_query("FastAPI dependencies")
    assert "FastAPI dependencies" in q1

    q2 = SearchEngine.build_search_query("Docker", tech_filter="docker")
    assert "Docker" in q2
    assert "official documentation" in q2 or "docs" in q2


def test_search_engine_with_mock():
    mock_ddg_results = [
        {"title": "FastAPI Guide", "href": "https://fastapi.tiangolo.com/guide", "body": "Official guide"},
        {"title": "FastAPI Blog", "href": "https://medium.com/fastapi-post", "body": "Unofficial post"},
    ]

    with patch("docscout.discovery.search_engine.DDGS") as mock_ddgs_class:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = mock_ddg_results
        mock_ddgs_class.return_value = mock_instance

        results = SearchEngine.search("FastAPI", max_results=5, min_confidence=0.50)
        assert len(results) == 1
        assert results[0].url == "https://fastapi.tiangolo.com/guide"
        assert results[0].is_official_domain is True
