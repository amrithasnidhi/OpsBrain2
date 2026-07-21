# compliance/rules.py
"""
Compliance rules for industrial equipment.

These rules are checked against claims in the knowledge graph.
Each rule specifies a standard, requirement, parameter_name to match,
and a threshold value for comparison.

Rules are designed to match parameters in the existing dataset:
- PSV-101: relief_pressure_psi, inspection_interval (from fixtures)
- PUMP-203: inspection_interval_months
- HX-301: cleaning_frequency
"""

COMPLIANCE_RULES = [
    # PSV inspection requirement - matches PSV-101 data
    {
        "standard": "OSHA 29 CFR 1910.119",
        "requirement": "PSV inspection every 12 months",
        "parameter_name": "inspection_interval",
        "equipment_pattern": "PSV",
        "threshold": 12,
        "comparison": "max_months"
    },
    # Pressure vessel inspection - Factory Act India
    {
        "standard": "Factory Act India",
        "requirement": "Pressure vessel inspection every 12 months",
        "parameter_name": "inspection_interval_months",
        "equipment_pattern": "PUMP",
        "threshold": 12,
        "comparison": "max_months"
    },
    # Bearing inspection for rotating equipment
    {
        "standard": "API 610",
        "requirement": "Pump bearing inspection every 6 months",
        "parameter_name": "inspection_interval_months",
        "equipment_pattern": "PUMP",
        "threshold": 6,
        "comparison": "max_months"
    },
    # Heat exchanger cleaning frequency
    {
        "standard": "TEMA Standards",
        "requirement": "Heat exchanger tube cleaning quarterly minimum",
        "parameter_name": "cleaning_frequency",
        "equipment_pattern": "HX",
        "threshold": 3,
        "comparison": "frequency_months"
    },
    # Relief valve setpoint verification
    {
        "standard": "ASME PTC 25",
        "requirement": "Relief valve setpoint within 3% of nameplate",
        "parameter_name": "relief_pressure_psi",
        "equipment_pattern": "PSV",
        "threshold": 3,
        "comparison": "percent_deviation"
    },
    # Fire safety drills
    {
        "standard": "OISD-GDN-206",
        "requirement": "Fire safety drill every 6 months",
        "parameter_name": "fire_drill_interval_months",
        "equipment_pattern": None,
        "threshold": 6,
        "comparison": "max_months"
    },
    # Compressor discharge pressure limits
    {
        "standard": "API 618",
        "requirement": "Compressor discharge pressure within design limits",
        "parameter_name": "max_discharge_pressure_psi",
        "equipment_pattern": "C-",
        "threshold": 300,
        "comparison": "max_value"
    },
    # Vibration monitoring frequency
    {
        "standard": "ISO 10816",
        "requirement": "Rotating equipment vibration check monthly",
        "parameter_name": "vibration_monitoring",
        "equipment_pattern": "PUMP",
        "threshold": 1,
        "comparison": "max_months"
    },
]
