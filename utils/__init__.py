"""
Package d'utilitaires pour l'analyse des systèmes d'attente.
"""

from .analysis_utils import (
    # Export
    export_to_csv,
    export_to_json,
    create_results_summary,
    
    # Stabilité
    StabilityResult,
    analyze_stability,
    generate_stability_map,
    find_critical_lambda,
    
    # Intervalles de confiance
    confidence_interval,
    percentile,
    
    # Équité
    gini_coefficient,
    jain_fairness_index,
    coefficient_of_variation,
    
    # Théorie
    erlang_c_probability,
    theoretical_mmk_waiting_time,
    theoretical_mm1_waiting_time,
    theoretical_tandem_sojourn,
    
    # Rapports
    generate_simulation_report,
)

__all__ = [
    'export_to_csv',
    'export_to_json',
    'create_results_summary',
    'StabilityResult',
    'analyze_stability',
    'generate_stability_map',
    'find_critical_lambda',
    'confidence_interval',
    'percentile',
    'gini_coefficient',
    'jain_fairness_index',
    'coefficient_of_variation',
    'erlang_c_probability',
    'theoretical_mmk_waiting_time',
    'theoretical_mm1_waiting_time',
    'theoretical_tandem_sojourn',
    'generate_simulation_report',
]
