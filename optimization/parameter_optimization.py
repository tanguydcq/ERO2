#!/usr/bin/env python3
"""
Module d'optimisation des paramètres du système de files d'attente.

Ce module implémente la recherche de paramètres optimaux en utilisant
scipy.optimize, comme recommandé par le coach (16/12/2025).

Fonctions principales :
- Définition de fonctions objectif (coût, temps, rejet)
- Recherche de paramètres optimaux sous contraintes
- Analyse de sensibilité

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution, Bounds
from scipy.stats import norm
from typing import Dict, Tuple, Callable, Optional, List
from dataclasses import dataclass
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tandem_queue_simulation import TandemQueueSimulator, run_multiple_simulations
from tandem_queue_finite import FiniteQueueSimulator


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================

@dataclass
class OptimizationResult:
    """Résultat d'une optimisation."""
    optimal_params: Dict[str, float]
    optimal_cost: float
    metrics: Dict[str, float]
    convergence_info: Dict
    sensitivity: Optional[Dict] = None


@dataclass
class CostWeights:
    """Poids pour la fonction de coût multi-objectif."""
    w_sojourn: float = 1.0      # Poids temps de séjour
    w_reject: float = 10.0      # Poids taux de rejet (pénalité)
    w_loss: float = 20.0        # Poids taux de perte (page blanche)
    w_server: float = 0.5       # Coût par serveur
    w_capacity: float = 0.1     # Coût par unité de capacité


# =============================================================================
# FONCTIONS OBJECTIF
# =============================================================================

def evaluate_system(
    K: int,
    ks: int, 
    kf: int,
    lambda_rate: float,
    mu1: float,
    mu2: float,
    n_trajectories: int = 100,
    jobs_per_trajectory: int = 2000,
    seed: int = 42
) -> Dict[str, float]:
    """
    Évalue les performances d'un système avec les paramètres donnés.
    
    Returns:
        Dictionnaire avec les métriques moyennes
    """
    # Simulation avec files finies
    simulator = FiniteQueueSimulator(
        lambda_rate=lambda_rate,
        mu1=mu1, 
        mu2=mu2,
        K=K,
        ks=ks,
        kf=kf
    )
    
    sojourn_times = []
    reject_counts = []
    loss_counts = []
    total_arrivals = []
    
    np.random.seed(seed)
    
    for i in range(n_trajectories):
        results = simulator.run(max_jobs=jobs_per_trajectory)
        
        if results['completed_jobs']:
            sojourn_times.extend([j.sojourn_time() for j in results['completed_jobs']])
        
        reject_counts.append(results['rejected_count'])
        loss_counts.append(results['lost_count'])
        total_arrivals.append(results['total_arrivals'])
    
    # Calcul des métriques
    mean_sojourn = np.mean(sojourn_times) if sojourn_times else float('inf')
    var_sojourn = np.var(sojourn_times) if sojourn_times else float('inf')
    
    total_rejects = sum(reject_counts)
    total_losses = sum(loss_counts)
    total_arr = sum(total_arrivals)
    
    reject_rate = total_rejects / total_arr if total_arr > 0 else 0
    loss_rate = total_losses / total_arr if total_arr > 0 else 0
    
    return {
        'mean_sojourn': mean_sojourn,
        'var_sojourn': var_sojourn,
        'reject_rate': reject_rate,
        'loss_rate': loss_rate,
        'throughput': len(sojourn_times) / (n_trajectories * jobs_per_trajectory / lambda_rate)
    }


def cost_function(
    params: np.ndarray,
    fixed_params: Dict,
    weights: CostWeights,
    n_trajectories: int = 50
) -> float:
    """
    Fonction de coût à minimiser.
    
    Args:
        params: [K, ks, kf] - paramètres à optimiser
        fixed_params: {'lambda_rate', 'mu1', 'mu2'} - paramètres fixes
        weights: Poids de la fonction de coût
        n_trajectories: Nombre de trajectoires pour l'évaluation
    
    Returns:
        Coût total (à minimiser)
    """
    K = max(1, int(round(params[0])))
    ks = max(K, int(round(params[1])))
    kf = max(1, int(round(params[2])))
    
    try:
        metrics = evaluate_system(
            K=K, ks=ks, kf=kf,
            lambda_rate=fixed_params['lambda_rate'],
            mu1=fixed_params['mu1'],
            mu2=fixed_params['mu2'],
            n_trajectories=n_trajectories,
            jobs_per_trajectory=1000
        )
        
        # Fonction de coût multi-objectif
        cost = (
            weights.w_sojourn * metrics['mean_sojourn'] +
            weights.w_reject * metrics['reject_rate'] * 100 +  # En pourcentage
            weights.w_loss * metrics['loss_rate'] * 100 +
            weights.w_server * K +
            weights.w_capacity * (ks + kf)
        )
        
        return cost
        
    except Exception as e:
        print(f"Erreur d'évaluation: {e}")
        return float('inf')


# =============================================================================
# OPTIMISATION
# =============================================================================

def optimize_parameters(
    lambda_rate: float,
    mu1: float,
    mu2: float,
    weights: Optional[CostWeights] = None,
    bounds: Optional[Dict] = None,
    method: str = 'differential_evolution',
    n_trajectories: int = 50,
    verbose: bool = True
) -> OptimizationResult:
    """
    Trouve les paramètres optimaux (K, ks, kf).
    
    Args:
        lambda_rate: Taux d'arrivée
        mu1: Taux de service station 1
        mu2: Taux de service station 2
        weights: Poids de la fonction de coût
        bounds: Bornes des paramètres {'K': (min, max), 'ks': ..., 'kf': ...}
        method: 'differential_evolution' ou 'minimize'
        n_trajectories: Trajectoires par évaluation
        verbose: Afficher progression
    
    Returns:
        OptimizationResult avec les paramètres optimaux
    """
    if weights is None:
        weights = CostWeights()
    
    if bounds is None:
        bounds = {
            'K': (1, 10),
            'ks': (5, 100),
            'kf': (3, 50)
        }
    
    fixed_params = {
        'lambda_rate': lambda_rate,
        'mu1': mu1,
        'mu2': mu2
    }
    
    # Bornes pour l'optimiseur
    param_bounds = [
        bounds['K'],
        bounds['ks'],
        bounds['kf']
    ]
    
    if verbose:
        print("="*60)
        print("OPTIMISATION DES PARAMÈTRES")
        print("="*60)
        print(f"Paramètres fixes: λ={lambda_rate}, μ1={mu1}, μ2={mu2}")
        print(f"Poids: sojourn={weights.w_sojourn}, reject={weights.w_reject}, loss={weights.w_loss}")
        print(f"Méthode: {method}")
        print("-"*60)
    
    if method == 'differential_evolution':
        result = differential_evolution(
            cost_function,
            bounds=param_bounds,
            args=(fixed_params, weights, n_trajectories),
            maxiter=50,
            tol=0.01,
            seed=42,
            workers=1,
            updating='deferred',
            polish=True
        )
    else:
        x0 = [3, 20, 10]  # Point de départ
        result = minimize(
            cost_function,
            x0=x0,
            args=(fixed_params, weights, n_trajectories),
            method='Nelder-Mead',
            options={'maxiter': 100}
        )
    
    # Extraire les paramètres optimaux
    K_opt = max(1, int(round(result.x[0])))
    ks_opt = max(K_opt, int(round(result.x[1])))
    kf_opt = max(1, int(round(result.x[2])))
    
    # Évaluation finale avec plus de trajectoires
    final_metrics = evaluate_system(
        K=K_opt, ks=ks_opt, kf=kf_opt,
        lambda_rate=lambda_rate,
        mu1=mu1, mu2=mu2,
        n_trajectories=200,
        jobs_per_trajectory=2000
    )
    
    optimal_params = {
        'K': K_opt,
        'ks': ks_opt,
        'kf': kf_opt
    }
    
    if verbose:
        print(f"\n✅ PARAMÈTRES OPTIMAUX TROUVÉS:")
        print(f"   K  = {K_opt} serveurs")
        print(f"   ks = {ks_opt} (capacité station 1)")
        print(f"   kf = {kf_opt} (capacité station 2)")
        print(f"\n📊 MÉTRIQUES RÉSULTANTES:")
        print(f"   Temps de séjour moyen: {final_metrics['mean_sojourn']:.3f}")
        print(f"   Taux de rejet: {final_metrics['reject_rate']*100:.2f}%")
        print(f"   Taux de perte: {final_metrics['loss_rate']*100:.2f}%")
        print(f"   Coût final: {result.fun:.3f}")
    
    return OptimizationResult(
        optimal_params=optimal_params,
        optimal_cost=result.fun,
        metrics=final_metrics,
        convergence_info={
            'success': result.success if hasattr(result, 'success') else True,
            'iterations': result.nit if hasattr(result, 'nit') else 0,
            'function_evaluations': result.nfev if hasattr(result, 'nfev') else 0
        }
    )


# =============================================================================
# ANALYSE DE SENSIBILITÉ
# =============================================================================

def sensitivity_analysis(
    base_params: Dict[str, float],
    fixed_params: Dict[str, float],
    param_to_vary: str,
    variation_range: Tuple[float, float],
    n_points: int = 10,
    n_trajectories: int = 100
) -> Dict[str, List]:
    """
    Analyse la sensibilité d'une métrique à un paramètre.
    
    Args:
        base_params: Paramètres de base {'K', 'ks', 'kf'}
        fixed_params: {'lambda_rate', 'mu1', 'mu2'}
        param_to_vary: Nom du paramètre à faire varier
        variation_range: (min, max) pour le paramètre
        n_points: Nombre de points d'évaluation
        n_trajectories: Trajectoires par point
    
    Returns:
        Dictionnaire avec les valeurs du paramètre et les métriques
    """
    param_values = np.linspace(variation_range[0], variation_range[1], n_points)
    
    results = {
        'param_values': [],
        'mean_sojourn': [],
        'var_sojourn': [],
        'reject_rate': [],
        'loss_rate': []
    }
    
    for val in param_values:
        test_params = base_params.copy()
        test_params[param_to_vary] = int(round(val)) if param_to_vary in ['K', 'ks', 'kf'] else val
        
        metrics = evaluate_system(
            K=test_params.get('K', base_params['K']),
            ks=test_params.get('ks', base_params['ks']),
            kf=test_params.get('kf', base_params['kf']),
            lambda_rate=fixed_params['lambda_rate'],
            mu1=fixed_params['mu1'],
            mu2=fixed_params['mu2'],
            n_trajectories=n_trajectories
        )
        
        results['param_values'].append(val)
        results['mean_sojourn'].append(metrics['mean_sojourn'])
        results['var_sojourn'].append(metrics['var_sojourn'])
        results['reject_rate'].append(metrics['reject_rate'])
        results['loss_rate'].append(metrics['loss_rate'])
    
    return results


# =============================================================================
# PARETO FRONT (OPTIMISATION MULTI-OBJECTIF)
# =============================================================================

def compute_pareto_front(
    lambda_rate: float,
    mu1: float,
    mu2: float,
    n_samples: int = 100,
    n_trajectories: int = 50
) -> List[Dict]:
    """
    Calcule le front de Pareto pour le compromis temps/coût/fiabilité.
    
    Returns:
        Liste des solutions non-dominées
    """
    solutions = []
    
    # Échantillonnage aléatoire des paramètres
    np.random.seed(42)
    
    for _ in range(n_samples):
        K = np.random.randint(1, 8)
        ks = np.random.randint(K, 50)
        kf = np.random.randint(1, 30)
        
        metrics = evaluate_system(
            K=K, ks=ks, kf=kf,
            lambda_rate=lambda_rate,
            mu1=mu1, mu2=mu2,
            n_trajectories=n_trajectories
        )
        
        solutions.append({
            'K': K, 'ks': ks, 'kf': kf,
            'sojourn': metrics['mean_sojourn'],
            'reject_rate': metrics['reject_rate'],
            'loss_rate': metrics['loss_rate'],
            'cost': K * 0.5 + (ks + kf) * 0.1  # Coût infrastructure
        })
    
    # Filtrage des solutions dominées
    pareto_front = []
    for sol in solutions:
        dominated = False
        for other in solutions:
            if (other['sojourn'] <= sol['sojourn'] and
                other['reject_rate'] <= sol['reject_rate'] and
                other['loss_rate'] <= sol['loss_rate'] and
                other['cost'] <= sol['cost'] and
                (other['sojourn'] < sol['sojourn'] or
                 other['reject_rate'] < sol['reject_rate'] or
                 other['loss_rate'] < sol['loss_rate'] or
                 other['cost'] < sol['cost'])):
                dominated = True
                break
        if not dominated:
            pareto_front.append(sol)
    
    return pareto_front


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("OPTIMISATION DES PARAMÈTRES DU SYSTÈME DE FILES D'ATTENTE")
    print("="*70)
    
    # Paramètres de référence
    lambda_rate = 4.0
    mu1 = 2.0
    mu2 = 5.0
    
    # Optimisation avec poids par défaut
    print("\n📍 Scénario 1: Équilibre standard")
    result1 = optimize_parameters(
        lambda_rate=lambda_rate,
        mu1=mu1,
        mu2=mu2,
        weights=CostWeights(w_sojourn=1.0, w_reject=10.0, w_loss=20.0),
        n_trajectories=30
    )
    
    # Optimisation priorisant le temps
    print("\n📍 Scénario 2: Priorité au temps de réponse")
    result2 = optimize_parameters(
        lambda_rate=lambda_rate,
        mu1=mu1,
        mu2=mu2,
        weights=CostWeights(w_sojourn=5.0, w_reject=5.0, w_loss=10.0, w_server=0.1),
        n_trajectories=30
    )
    
    # Optimisation priorisant la fiabilité
    print("\n📍 Scénario 3: Priorité à la fiabilité (zéro perte)")
    result3 = optimize_parameters(
        lambda_rate=lambda_rate,
        mu1=mu1,
        mu2=mu2,
        weights=CostWeights(w_sojourn=0.5, w_reject=15.0, w_loss=50.0),
        n_trajectories=30
    )
    
    # Résumé comparatif
    print("\n" + "="*70)
    print("COMPARAISON DES SCÉNARIOS")
    print("="*70)
    print(f"{'Scénario':<25} {'K':>4} {'ks':>4} {'kf':>4} {'E[W]':>8} {'Rejet%':>8} {'Perte%':>8}")
    print("-"*70)
    
    for name, res in [("Équilibre", result1), ("Temps rapide", result2), ("Fiabilité max", result3)]:
        p = res.optimal_params
        m = res.metrics
        print(f"{name:<25} {p['K']:>4} {p['ks']:>4} {p['kf']:>4} "
              f"{m['mean_sojourn']:>8.3f} {m['reject_rate']*100:>7.2f}% {m['loss_rate']*100:>7.2f}%")
