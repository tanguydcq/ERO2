"""
Module d'optimisation des paramètres du système de files d'attente.

Ce module fournit des outils pour :
- Trouver les paramètres optimaux (K, ks, kf)
- Analyser la sensibilité aux paramètres
- Calculer le front de Pareto pour l'optimisation multi-objectif

Usage:
    from optimization.parameter_optimization import optimize_parameters, CostWeights
    
    result = optimize_parameters(
        lambda_rate=4.0,
        mu1=2.0,
        mu2=5.0,
        weights=CostWeights(w_sojourn=1.0, w_reject=10.0)
    )
"""

from .parameter_optimization import (
    OptimizationResult,
    CostWeights,
    evaluate_system,
    cost_function,
    optimize_parameters,
    sensitivity_analysis,
    compute_pareto_front
)

__all__ = [
    'OptimizationResult',
    'CostWeights',
    'evaluate_system',
    'cost_function',
    'optimize_parameters',
    'sensitivity_analysis',
    'compute_pareto_front'
]
