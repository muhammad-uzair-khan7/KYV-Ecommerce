import pytest
import pytest_asyncio
import respx
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from state_container import AssessmentGraphState
from kyb_screening import kyb_sreening_node
from contract_analysis import contract_analysis_node
from risk_scoring import risk_scoring_node, DynamicRiskEvaluationEngine
from human_review import human_review_queue_node
from orchestrator import compiled_graph

from tests.mock_yente import MOCK_YENTE_CLEAN, MOCK_YENTE_FLAGGED, MOCK_YENTE_BLOCKED
from tests.mock_pinecone import MOCK_PINECONE_HITS


# ── Base state ─────────────────────────────────────────────────────────────────

def base_state() -> AssessmentGraphState:
    return {
        "messages": [],
        "vendor_id": "vendor-test-123",
        "tenant_id": "tenant-test-abc",
        "company_name": "TechVendor Inc",
        "country_iso": "PK",
        "vendor_type": "saas_software",
        "kyb_status": "",
        "parsed_contracts": [],
        "watchlist_flags": [],
        "computed_risk_vector": {},
        "next_action_node": ""
    }


# ── KYB Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_kyb_returns_clean():
    """Clean vendor should return CLEAN with no flags"""
    respx.post("http://yente_api:8000/match/default").mock(
        return_value=httpx.Response(200, json=MOCK_YENTE_CLEAN)
    )

    state = base_state()
    result = await kyb_sreening_node(state)

    assert result["kyb_status"] == "CLEAN"
    assert result["watchlist_flags"] == []
    assert len(result["messages"]) == 1


@pytest.mark.asyncio
@respx.mock
async def test_kyb_returns_flagged_on_pep():
    """PEP match should return FLAGGED"""
    respx.post("http://yente_api:8000/match/default").mock(
        return_value=httpx.Response(200, json=MOCK_YENTE_FLAGGED)
    )

    state = base_state()
    result = await kyb_sreening_node(state)

    assert result["kyb_status"] == "FLAGGED"
    assert len(result["watchlist_flags"]) == 1
    assert result["watchlist_flags"][0]["is_pep"] == True


@pytest.mark.asyncio
@respx.mock
async def test_kyb_returns_blocked_on_sanctions():
    """Sanctions match should return BLOCKED"""
    respx.post("http://yente_api:8000/match/default").mock(
        return_value=httpx.Response(200, json=MOCK_YENTE_BLOCKED)
    )

    state = base_state()
    result = await kyb_sreening_node(state)

    assert result["kyb_status"] == "BLOCKED"
    assert result["watchlist_flags"][0]["is_sanctioned"] == True


@pytest.mark.asyncio
@respx.mock
async def test_kyb_handles_yente_down():
    """If Yente is unreachable, should return PENDING_RETRY not crash"""
    respx.post("http://yente_api:8000/match/default").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    state = base_state()
    result = await kyb_sreening_node(state)

    assert result["kyb_status"] == "PENDING_RETRY"


# ── Contract Analysis Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contract_analysis_with_mock_pinecone():
    """Contract node should extract clause analysis from retrieved chunks"""
    with patch("contract_analysis.query_hybrid_contract_context",
               new=AsyncMock(return_value=MOCK_PINECONE_HITS)):
        with patch("contract_analysis._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_embed = MagicMock()
            mock_embed.embeddings = [MagicMock(values=[0.1] * 768)]
            mock_client.models.embed_content.return_value = mock_embed

            mock_response = MagicMock()
            mock_response.text = """{
                "liability_cap_found": true,
                "liability_cap_amount": "$500,000",
                "force_majeure_present": true,
                "data_processing_agreement": true,
                "auto_renewal_clause": false,
                "termination_for_convenience": true,
                "indemnification_scope": "narrow",
                "governing_law": "Pakistan",
                "high_risk_clauses": [],
                "overall_contract_risk": "LOW"
            }"""
            mock_client.models.generate_content.return_value = mock_response

            state = base_state()
            result = await contract_analysis_node(state)

    assert len(result["parsed_contracts"]) == 1
    analysis = result["parsed_contracts"][0]["clause_analysis"]
    assert analysis["liability_cap_found"] == True
    assert analysis["overall_contract_risk"] == "LOW"


@pytest.mark.asyncio
async def test_contract_analysis_no_documents():
    """If Pinecone returns nothing, should handle gracefully"""
    with patch("contract_analysis.query_hybrid_contract_context",
               new=AsyncMock(return_value=[])):
        with patch("contract_analysis._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_embed = MagicMock()
            mock_embed.embeddings = [MagicMock(values=[0.1] * 768)]
            mock_client.models.embed_content.return_value = mock_embed

            state = base_state()
            result = await contract_analysis_node(state)

    assert result["parsed_contracts"] == []


# ── Risk Scoring Tests ─────────────────────────────────────────────────────────

def test_risk_engine_low_risk():
    """Clean vendor with mitigations should score low"""
    scores = DynamicRiskEvaluationEngine.calculate_vendor_scores(
        category_weights={"cyber": 0.25, "compliance": 0.25,
                          "financial": 0.25, "operational": 0.25},
        domain_scores={"cyber": 10, "compliance": 5,
                       "financial": 15, "operational": 10},
        verified_mitigations=[
            {"is_verified": True, "reduction_coefficient": 0.10},
            {"is_verified": True, "reduction_coefficient": 0.08},
        ]
    )
    assert scores["inherent_risk"] <= 25
    assert scores["residual_risk"] < scores["inherent_risk"]


def test_risk_engine_weights_must_sum_to_one():
    """Bad weights should raise ValueError"""
    with pytest.raises(ValueError):
        DynamicRiskEvaluationEngine.calculate_vendor_scores(
            category_weights={"cyber": 0.50, "compliance": 0.50,
                              "financial": 0.50, "operational": 0.50},
            domain_scores={"cyber": 10, "compliance": 5,
                           "financial": 15, "operational": 10},
            verified_mitigations=[]
        )


def test_risk_engine_mitigation_capped_at_80_percent():
    """Even with many mitigations, residual can't drop below 20% of inherent"""
    scores = DynamicRiskEvaluationEngine.calculate_vendor_scores(
        category_weights={"cyber": 0.25, "compliance": 0.25,
                          "financial": 0.25, "operational": 0.25},
        domain_scores={"cyber": 80, "compliance": 80,
                       "financial": 80, "operational": 80},
        verified_mitigations=[
            {"is_verified": True, "reduction_coefficient": 0.50},
            {"is_verified": True, "reduction_coefficient": 0.50},
            {"is_verified": True, "reduction_coefficient": 0.50},
        ]
    )
    assert scores["residual_risk"] == int(round(scores["inherent_risk"] * 0.20))


def test_risk_scoring_node_clean_vendor():
    """Full node test with clean state"""
    state = base_state()
    state["kyb_status"] = "CLEAN"
    state["watchlist_flags"] = []
    state["parsed_contracts"] = [{
        "clause_analysis": {
            "data_processing_agreement": True,
            "liability_cap_found": True,
            "governing_law": "Pakistan",
            "overall_contract_risk": "LOW",
            "auto_renewal_clause": False,
            "termination_for_convenience": True
        }
    }]

    result = risk_scoring_node(state)
    vector = result["computed_risk_vector"]

    assert "overall_score" in vector
    assert vector["overall_score"] <= 25


# ── Full Graph Flow Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_full_graph_clean_vendor_reaches_end():
    """Full happy path: clean KYB → contract analysis → risk scoring → END"""
    respx.post("http://yente_api:8000/match/default").mock(
        return_value=httpx.Response(200, json=MOCK_YENTE_CLEAN)
    )

    with patch("contract_analysis.query_hybrid_contract_context",
               new=AsyncMock(return_value=MOCK_PINECONE_HITS)):
        with patch("contract_analysis._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_embed = MagicMock()
            mock_embed.embeddings = [MagicMock(values=[0.1] * 768)]
            mock_client.models.embed_content.return_value = mock_embed

            mock_response = MagicMock()
            mock_response.text = """{
                "liability_cap_found": true,
                "liability_cap_amount": "$500,000",
                "force_majeure_present": true,
                "data_processing_agreement": true,
                "auto_renewal_clause": false,
                "termination_for_convenience": true,
                "indemnification_scope": "narrow",
                "governing_law": "Pakistan",
                "high_risk_clauses": [],
                "overall_contract_risk": "LOW"
            }"""
            mock_client.models.generate_content.return_value = mock_response

            with patch("human_review.asyncpg.connect", new=AsyncMock()):
                state = base_state()
                result = await compiled_graph.ainvoke(state)

    assert result["kyb_status"] == "CLEAN"
    assert result["computed_risk_vector"]["overall_score"] <= 25


@pytest.mark.asyncio
@respx.mock
async def test_full_graph_blocked_vendor_goes_to_human_review():
    """Blocked vendor should skip contract analysis and go straight to HumanReview"""
    respx.post("http://yente_api:8000/match/default").mock(
        return_value=httpx.Response(200, json=MOCK_YENTE_BLOCKED)
    )

    with patch("human_review.asyncpg.connect", new=AsyncMock()):
        state = base_state()
        result = await compiled_graph.ainvoke(state)

    assert result["kyb_status"] == "BLOCKED"
    assert result["parsed_contracts"] == []