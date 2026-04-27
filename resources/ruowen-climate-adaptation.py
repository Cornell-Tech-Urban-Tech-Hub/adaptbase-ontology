# ontology/schema.py

ONTOLOGY = {

    # ==============================
    # URBAN SYSTEM LAYER
    # ==============================

    "UrbanSystem": {

        "City": {
            "properties": [
                "name", "administrative_level",
                "climate_zone", "population",
                "gdp_per_capita", "region",
                "is_case_study"
            ]
        },

        "UrbanZone": {
            "description": "Functional spatial units within a city",
            "properties": [
                "zone_type",
                "area_km2",
                "population_density",
                "land_use_type"
            ]
        },

        "Infrastructure": {
            "description": "Socio-technical infrastructure (green/grey/blue)",
            "properties": [
                "infra_type",
                "infra_color",
                "capacity",
                "condition",
                "service_coverage"
            ]
        },

        "ExposureUnit": {
            "description": "Population or asset exposed to hazards",
            "properties": [
                "population_count",
                "asset_value",
                "vulnerable_ratio",
                "social_capital_index"
            ]
        }
    },

    # ==============================
    # CLIMATE RISK LAYER
    # ==============================

    "ClimateRisk": {

        "ClimateHazard": {
            "properties": [
                "hazard_type",
                "frequency",
                "severity",
                "trend",
                "return_period",
                "spatial_extent"
            ]
        },

        "Vulnerability": {
            "description": "Exposure, sensitivity, adaptive capacity",
            "properties": [
                "vuln_type",
                "exposure_score",
                "sensitivity_score",
                "adaptive_capacity_score",
                "affected_group"
            ]
        }
    },

    # ==============================
    # GOVERNANCE LAYER
    # ==============================

    "Governance": {

        "Actor": {
            "properties": [
                "name",
                "sector",
                "role",
                "authority_level",
                "resources",
                "is_bridge_organization"
            ]
        },

        "Policy": {
            "properties": [
                "policy_name",
                "policy_type",
                "level",
                "year_issued",
                "year_expired",
                "legal_binding"
            ]
        },

        "Mechanism": {
            "description": "Financial, regulatory, or technical enablers",
            "properties": [
                "mechanism_type",
                "source_of_funding",
                "legal_basis",
                "scale_usd"
            ]
        },

        "Constraint": {
            "properties": [
                "constraint_type",
                "severity_score",
                "affected_stakeholder",
                "is_structural"
            ]
        }
    },

    # ==============================
    # INTERVENTION LAYER
    # ==============================

    "Intervention": {

        "AdaptationAction": {
            "properties": [
                "action_name",
                "status",
                "spatial_scale",
                "adaptation_type",
                "start_year",
                "end_year",
                "cost_usd",
                "co_benefits"
            ]
        }
    },

    # ==============================
    # EVALUATION & TIME LAYER
    # ==============================

    "Evaluation": {

        "Outcome": {
            "properties": [
                "outcome_type",
                "indicator",
                "value",
                "unit",
                "is_co_benefit",
                "evidence_quality"
            ]
        },

        "Indicator": {
            "properties": [
                "indicator_name",
                "unit",
                "baseline",
                "target",
                "data_source"
            ]
        },

        "ResilienceState": {
            "properties": [
                "resilience_type",
                "measurement",
                "recovery_time",
                "absorption_capacity",
                "transformation_capacity"
            ]
        },

        "TimePoint": {
            "properties": [
                "year",
                "period",
                "policy_cycle"
            ]
        }
    },

    # ==============================
    # RELATIONSHIPS
    # ==============================

    "relationships": {

        # --- Urban Structure ---
        "HAS_ZONE":           {"domain": "City", "range": "UrbanZone"},
        "HAS_INFRASTRUCTURE": {"domain": "UrbanZone", "range": "Infrastructure"},
        "SERVES":             {"domain": "Infrastructure", "range": "ExposureUnit",
                               "properties": ["service_level"]},

        # --- Risk Chain ---
        "EXPERIENCES":        {"domain": "City", "range": "ClimateHazard"},
        "AFFECTS_ZONE":       {"domain": "ClimateHazard", "range": "UrbanZone",
                               "properties": ["impact_severity"]},
        "EXPOSES":            {"domain": "ClimateHazard", "range": "ExposureUnit"},
        "WORSENS":            {"domain": "ClimateHazard", "range": "Vulnerability"},
        "EXPERIENCES_VULN":   {"domain": "ExposureUnit", "range": "Vulnerability"},

        # --- Governance Structure ---
        "ISSUED_BY":          {"domain": "Policy", "range": "Actor"},
        "MANDATES":           {"domain": "Policy", "range": "AdaptationAction"},
        "IMPLEMENTS":         {"domain": "Actor", "range": "AdaptationAction"},
        "PARTICIPATES_IN":    {"domain": "Actor", "range": "AdaptationAction"},
        "COORDINATES_WITH":   {"domain": "Actor", "range": "Actor"},
        "REPORTS_TO":         {"domain": "Actor", "range": "Actor"},
        "MANAGES":            {"domain": "Actor", "range": "Mechanism"},
        "FACES":              {"domain": "Actor", "range": "Constraint"},

        # --- Core Causal Chain ---
        "LOCATED_IN":         {"domain": "AdaptationAction", "range": "City"},
        "TARGETS_ZONE":       {"domain": "AdaptationAction", "range": "UrbanZone"},
        "ADDRESSES":          {"domain": "AdaptationAction", "range": "ClimateHazard"},
        "REDUCES":            {"domain": "AdaptationAction", "range": "Vulnerability"},
        "IMPROVES":           {"domain": "AdaptationAction", "range": "Infrastructure"},
        "FACILITATED_BY":     {"domain": "AdaptationAction", "range": "Mechanism"},
        "HINDERED_BY":        {"domain": "AdaptationAction", "range": "Constraint"},
        "PRODUCES":           {"domain": "AdaptationAction", "range": "Outcome"},

        # --- Evaluation ---
        "MEASURES":           {"domain": "Indicator", "range": "Outcome"},
        "MONITORS":           {"domain": "Actor", "range": "Indicator"},
        "REFLECTS":           {"domain": "Outcome", "range": "ResilienceState"},

        # --- Temporal ---
        "STARTED_AT":         {"domain": "AdaptationAction", "range": "TimePoint"},
        "ISSUED_AT":          {"domain": "Policy", "range": "TimePoint"},
        "RECORDED_AT":        {"domain": "Indicator", "range": "TimePoint",
                               "properties": ["value"]}
    }
}