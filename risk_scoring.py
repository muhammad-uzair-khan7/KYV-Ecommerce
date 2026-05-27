from langchain_core.messages import AIMessage
from state_container import AssessmentGraphState

class DynamicRiskEvaluationEngine:
    @staticmethod
    def calculate_vendor_scores(
        category_weights:    dict[str, float],
        domain_scores:       dict[str, int],
        verified_mitigations: list[dict]
    ) -> dict[str, int]:

        if not abs(sum(category_weights.values()) - 1.0) < 1e-5:
            raise ValueError("Risk weights must sum to exactly 1.0")

        inherent_risk = sum(
            category_weights[d] * domain_scores[d]
            for d in ["cyber", "compliance", "financial", "operational"]
        )

        total_discount = 0.0
        for m in verified_mitigations:
            if m.get("is_verified", False):
                total_discount += float(m.get("reduction_coefficient", 0.0))

        total_discount  = min(total_discount, 0.8)
        residual_risk   = inherent_risk * (1.0 - total_discount)

        return {
            "inherent_risk": int(round(inherent_risk)),
            "residual_risk": int(round(residual_risk))
        }


WEIGHT_PROFILES = {
    "data_processor":    {"cyber": 0.40, "compliance": 0.30, "financial": 0.15, "operational": 0.15},
    "logistics":         {"cyber": 0.15, "compliance": 0.25, "financial": 0.20, "operational": 0.40},
    "saas_software":     {"cyber": 0.35, "compliance": 0.30, "financial": 0.20, "operational": 0.15},
    "financial_service": {"cyber": 0.20, "compliance": 0.45, "financial": 0.25, "operational": 0.10},
    "default":           {"cyber": 0.25, "compliance": 0.25, "financial": 0.25, "operational": 0.25},
}


def _derive_domain_scores(state: AssessmentGraphState) -> dict[str, int]:
<<<<<<< HEAD
    flags     = state.get("watchlist_flags", [])
    contracts = state.get("parsed_contracts", [])

    # Compliance score — driven by KYB flags
    if any(f.get("is_sanctioned") for f in flags):
        compliance = 100
    elif any(f.get("is_pep") for f in flags):
=======
    flags     = state.get("watchlist_flags", []) or []
    contracts = state.get("parsed_contracts", []) or []

    # Compliance score — driven by KYB flags
    if any(f.get("is_sanctioned") for f in flags if f is not None):
        compliance = 100
    elif any(f.get("is_pep") for f in flags if f is not None):
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
        compliance = 65
    elif flags:
        compliance = 40
    else:
        compliance = 5

    # Cyber score — derived from contract signals (replace with UpGuard in prod)
    cyber = 10
<<<<<<< HEAD
    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if not analysis.get("data_processing_agreement"):
            cyber += 30
        if analysis.get("overall_contract_risk") == "HIGH":
            cyber += 20
=======
    if contracts and len(contracts) > 0:
        contract = contracts[0]
        if contract is not None:
            analysis = contract.get("clause_analysis", {}) or {}
            if not analysis.get("data_processing_agreement"):
                cyber += 30
            if analysis.get("overall_contract_risk") == "HIGH":
                cyber += 20
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

    # Financial — placeholder until Creditsafe feed is wired in
    financial = 15

    # Operational — derived from contract terms
    operational = 10
<<<<<<< HEAD
    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if not analysis.get("termination_for_convenience"):
            operational += 15
        if analysis.get("auto_renewal_clause"):
            operational += 10
=======
    if contracts and len(contracts) > 0:
        contract = contracts[0]
        if contract is not None:
            analysis = contract.get("clause_analysis", {}) or {}
            if not analysis.get("termination_for_convenience"):
                operational += 15
            if analysis.get("auto_renewal_clause"):
                operational += 10
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

    return {
        "cyber":       min(cyber, 100),
        "compliance":  min(compliance, 100),
        "financial":   min(financial, 100),
        "operational": min(operational, 100),
    }


def _derive_mitigations(state: AssessmentGraphState) -> list[dict]:
    mitigations = []
<<<<<<< HEAD
    contracts   = state.get("parsed_contracts", [])

    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if analysis.get("data_processing_agreement"):
            mitigations.append({"name": "DPA in place",          "is_verified": True, "reduction_coefficient": 0.10})
        if analysis.get("liability_cap_found"):
            mitigations.append({"name": "Liability cap",         "is_verified": True, "reduction_coefficient": 0.08})
        if analysis.get("governing_law"):
            mitigations.append({"name": "Governing law defined", "is_verified": True, "reduction_coefficient": 0.05})
=======
    contracts   = state.get("parsed_contracts", []) or []

    if contracts and len(contracts) > 0:
        contract = contracts[0]
        if contract is not None:
            analysis = contract.get("clause_analysis", {}) or {}
            if analysis.get("data_processing_agreement"):
                mitigations.append({"name": "DPA in place",          "is_verified": True, "reduction_coefficient": 0.10})
            if analysis.get("liability_cap_found"):
                mitigations.append({"name": "Liability cap",         "is_verified": True, "reduction_coefficient": 0.08})
            if analysis.get("governing_law"):
                mitigations.append({"name": "Governing law defined", "is_verified": True, "reduction_coefficient": 0.05})
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

    return mitigations


def risk_scoring_node(state: AssessmentGraphState) -> dict:
<<<<<<< HEAD
    vendor_id    = state["vendor_id"]
=======
    vendor_id    = state.get("vendor_id", "UNKNOWN")
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    vendor_type  = state.get("vendor_type", "default")
    weights      = WEIGHT_PROFILES.get(vendor_type, WEIGHT_PROFILES["default"])
    domain_scores = _derive_domain_scores(state)
    mitigations   = _derive_mitigations(state)

    scores = DynamicRiskEvaluationEngine.calculate_vendor_scores(
        category_weights=weights,
        domain_scores=domain_scores,
        verified_mitigations=mitigations
    )

    risk_vector = {
        "cyber":               domain_scores["cyber"],
        "sanctions":           domain_scores["compliance"],
        "financial":           domain_scores["financial"],
        "operational":         domain_scores["operational"],
        "inherent_score":      scores["inherent_risk"],
        "overall_score":       scores["residual_risk"],
        "vendor_type":         vendor_type,
        "weight_profile":      weights,
        "mitigations_applied": len(mitigations),
    }

    score = scores["residual_risk"]
    if   score <= 25: label = "LOW — fast-track eligible"
    elif score <= 50: label = "MEDIUM — annual review"
    elif score <= 75: label = "HIGH — EDD required"
    else:             label = "PROHIBITED — auto block"

    return {
        "computed_risk_vector": risk_vector,
        "messages": [AIMessage(content=
            f"Risk scoring complete for {vendor_id}. "
            f"Inherent: {scores['inherent_risk']} | Residual: {scores['residual_risk']}. "
            f"Classification: {label}."
<<<<<<< HEAD
        )]
=======
        )],
        "vendor_id": vendor_id,
        "vendor_type": vendor_type
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    }
