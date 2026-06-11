# from langchain_core.messages import AIMessage
# from state_container import AssessmentGraphState


# class DynamicRiskEvaluationEngine:
#     @staticmethod
#     def calculate_vendor_scores(
#         category_weights: dict[str, float],
#         domain_scores: dict[str, int],
#         verified_mitigations: list[dict]
#     ) -> dict[str, int]:

#         if not abs(sum(category_weights.values()) - 1.0) < 1e-5:
#             raise ValueError("Risk weights must sum to exactly 1.0")

#         inherent_risk = sum(
#             category_weights[d] * domain_scores[d]
#             for d in ["cyber", "compliance", "financial", "operational"]
#         )

#         total_discount = 0.0
#         for m in verified_mitigations:
#             if m.get("is_verified", False):
#                 total_discount += float(m.get("reduction_coefficient", 0.0))

#         total_discount = min(total_discount, 0.8)
#         residual_risk = inherent_risk * (1.0 - total_discount)

#         return {
#             "inherent_risk": int(round(inherent_risk)),
#             "residual_risk": int(round(residual_risk))
#         }


# WEIGHT_PROFILES = {
#     "data_processor": {"cyber": 0.40, "compliance": 0.30, "financial": 0.15, "operational": 0.15},
#     "logistics": {"cyber": 0.15, "compliance": 0.25, "financial": 0.20, "operational": 0.40},
#     "saas_software": {"cyber": 0.35, "compliance": 0.30, "financial": 0.20, "operational": 0.15},
#     "financial_service": {"cyber": 0.20, "compliance": 0.45, "financial": 0.25, "operational": 0.10},
#     "default": {"cyber": 0.25, "compliance": 0.25, "financial": 0.25, "operational": 0.25},
# }


# def _derive_domain_scores(state: AssessmentGraphState) -> dict[str, int]:
#     """Derive risk scores for each domain (cyber, compliance, financial, operational)"""
#     flags = state.get("watchlist_flags", [])
#     contracts = state.get("parsed_contracts", [])

#     # Compliance score — driven by KYB flags (0-100 scale)
#     if any(f.get("is_sanctioned") for f in flags if f is not None):
#         compliance = 100
#     elif any(f.get("is_pep") for f in flags if f is not None):
#         compliance = 70
#     elif flags:
#         compliance = 50
#     else:
#         compliance = 20  # Baseline for unknown vendor (was 5, too low)

#     # Cyber score — derived from contract signals (0-100 scale)
#     cyber = 30  # Baseline (was 10, insufficient)
#     if contracts and len(contracts) > 0:
#         contract = contracts[0]
#         if contract is not None:
#             analysis = contract.get("clause_analysis", {}) or {}
#             if not analysis.get("data_processing_agreement"):
#                 cyber += 25  # Missing DPA adds risk
#             if analysis.get("overall_contract_risk") == "HIGH":
#                 cyber += 20
#             # Contract found reduces cyber risk
#             cyber = max(cyber - 15, 15)

#     # Financial — baseline score (0-100 scale)
#     financial = 35  # Baseline (was 15)
#     # Could add credit score checks here in future

#     # Operational — derived from contract terms (0-100 scale)
#     operational = 30  # Baseline (was 10)
#     if contracts and len(contracts) > 0:
#         contract = contracts[0]
#         if contract is not None:
#             analysis = contract.get("clause_analysis", {}) or {}
#             if not analysis.get("termination_for_convenience"):
#                 operational += 20  # Can't terminate easily = higher risk
#             if not analysis.get("auto_renewal_clause"):
#                 operational -= 10  # No auto renewal = lower risk
#             # Good contract terms reduce operational risk
#             if analysis.get("liability_cap_found") and analysis.get("data_processing_agreement"):
#                 operational = max(operational - 15, 15)

#     return {
#         "cyber": min(cyber, 100),
#         "compliance": min(compliance, 100),
#         "financial": min(financial, 100),
#         "operational": min(operational, 100),
#     }


# def _derive_mitigations(state: AssessmentGraphState) -> list[dict]:
#     """Derive risk mitigations from contract analysis"""
#     mitigations = []
#     contracts = state.get("parsed_contracts", []) or []

#     if contracts and len(contracts) > 0:
#         contract = contracts[0]
#         if contract is not None:
#             analysis = contract.get("clause_analysis", {}) or {}
#             if analysis.get("data_processing_agreement"):
#                 mitigations.append({"name": "DPA in place", "is_verified": True, "reduction_coefficient": 0.10})
#             if analysis.get("liability_cap_found"):
#                 mitigations.append({"name": "Liability cap", "is_verified": True, "reduction_coefficient": 0.08})
#             if analysis.get("governing_law"):
#                 mitigations.append({"name": "Governing law defined", "is_verified": True, "reduction_coefficient": 0.05})

#     return mitigations


# def risk_scoring_node(state: AssessmentGraphState) -> dict:
#     """
#     Risk Scoring Node - Calculates vendor risk score based on multiple factors
#     """
#     vendor_id = state.get("vendor_id", "UNKNOWN")
#     vendor_type = state.get("vendor_type", "default")
#     weights = WEIGHT_PROFILES.get(vendor_type, WEIGHT_PROFILES["default"])
#     domain_scores = _derive_domain_scores(state)
#     mitigations = _derive_mitigations(state)

#     scores = DynamicRiskEvaluationEngine.calculate_vendor_scores(
#         category_weights=weights,
#         domain_scores=domain_scores,
#         verified_mitigations=mitigations
#     )

#     risk_vector = {
#         "cyber": domain_scores["cyber"],
#         "sanctions": domain_scores["compliance"],
#         "financial": domain_scores["financial"],
#         "operational": domain_scores["operational"],
#         "inherent_score": scores["inherent_risk"],
#         "overall_score": scores["residual_risk"],
#         "vendor_type": vendor_type,
#         "weight_profile": weights,
#         "mitigations_applied": len(mitigations),
#     }

#     score = scores["residual_risk"]
#     if score <= 25:
#         label = "LOW — fast-track eligible"
#     elif score <= 50:
#         label = "MEDIUM — annual review"
#     elif score <= 75:
#         label = "HIGH — EDD required"
#     else:
#         label = "PROHIBITED — auto block"

#     return {
#         "computed_risk_vector": risk_vector,
#         "messages": [AIMessage(content=
#             f"Risk scoring complete for {vendor_id}. "
#             f"Inherent: {scores['inherent_risk']} | Residual: {scores['residual_risk']}. "
#             f"Classification: {label}."
#         )],
#         "vendor_id": vendor_id,
#         "vendor_type": vendor_type,
#         "_risk_scoring_done": True
#     }


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
    flags     = state.get("watchlist_flags", [])
    contracts = state.get("parsed_contracts", [])

    # Compliance score — driven by KYB flags
    if any(f.get("is_sanctioned") for f in flags):
        compliance = 100
    elif any(f.get("is_pep") for f in flags):
        compliance = 65
    elif flags:
        compliance = 40
    else:
        compliance = 5

    # Cyber score — derived from contract signals (replace with UpGuard in prod)
    cyber = 10
    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if not analysis.get("data_processing_agreement"):
            cyber += 30
        if analysis.get("overall_contract_risk") == "HIGH":
            cyber += 20

    # Financial — placeholder until Creditsafe feed is wired in
    financial = 15

    # Operational — derived from contract terms
    operational = 10
    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if not analysis.get("termination_for_convenience"):
            operational += 15
        if analysis.get("auto_renewal_clause"):
            operational += 10

    return {
        "cyber":       min(cyber, 100),
        "compliance":  min(compliance, 100),
        "financial":   min(financial, 100),
        "operational": min(operational, 100),
    }


def _derive_mitigations(state: AssessmentGraphState) -> list[dict]:
    mitigations = []
    contracts   = state.get("parsed_contracts", [])

    if contracts:
        analysis = contracts[0].get("clause_analysis", {})
        if analysis.get("data_processing_agreement"):
            mitigations.append({"name": "DPA in place",          "is_verified": True, "reduction_coefficient": 0.10})
        if analysis.get("liability_cap_found"):
            mitigations.append({"name": "Liability cap",         "is_verified": True, "reduction_coefficient": 0.08})
        if analysis.get("governing_law"):
            mitigations.append({"name": "Governing law defined", "is_verified": True, "reduction_coefficient": 0.05})

    return mitigations


def risk_scoring_node(state: AssessmentGraphState) -> dict:
    vendor_id    = state["vendor_id"]
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
        )]
    }
