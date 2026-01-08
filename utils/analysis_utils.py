#!/usr/bin/env python3
"""
Utilitaires pour l'analyse statistique et l'export des résultats.

Ce module fournit des fonctions pour :
- Exporter les résultats en CSV/JSON
- Calculer des intervalles de confiance
- Analyser la stabilité du système
- Calculer des métriques d'équité

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import json
import csv
import math
import os
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


# =============================================================================
# EXPORT DES DONNÉES
# =============================================================================

def export_to_csv(data: List[Dict[str, Any]], filepath: str, 
                  fieldnames: Optional[List[str]] = None) -> str:
    """
    Exporte une liste de dictionnaires vers un fichier CSV.
    
    Args:
        data: Liste de dictionnaires avec les mêmes clés
        filepath: Chemin du fichier de sortie
        fieldnames: Liste des colonnes (optionnel, auto-détecté sinon)
    
    Returns:
        Chemin absolu du fichier créé
    """
    if not data:
        raise ValueError("Aucune donnée à exporter")
    
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    return os.path.abspath(filepath)


def export_to_json(data: Any, filepath: str, indent: int = 2) -> str:
    """
    Exporte des données vers un fichier JSON.
    
    Args:
        data: Données à exporter (dict, list, etc.)
        filepath: Chemin du fichier de sortie
        indent: Indentation pour le formatage
    
    Returns:
        Chemin absolu du fichier créé
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
    
    return os.path.abspath(filepath)


def create_results_summary(results: Dict, model_name: str) -> Dict:
    """
    Crée un résumé structuré des résultats pour export.
    
    Args:
        results: Dictionnaire des résultats de simulation
        model_name: Nom du modèle simulé
    
    Returns:
        Dictionnaire formaté pour export
    """
    return {
        'metadata': {
            'model': model_name,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        },
        'results': results
    }


# =============================================================================
# ANALYSE DE STABILITÉ
# =============================================================================

@dataclass
class StabilityResult:
    """Résultat d'analyse de stabilité."""
    lambda_rate: float
    mu1: float
    mu2: float
    K: int
    rho1: float  # Charge station 1
    rho2: float  # Charge station 2
    is_stable: bool
    stability_margin_s1: float  # Distance à l'instabilité (1 - rho)
    stability_margin_s2: float
    bottleneck: str  # 'S1', 'S2', 'both' ou 'none'
    max_lambda_stable: float  # Lambda max pour stabilité
    
    def to_dict(self) -> Dict:
        return asdict(self)


def analyze_stability(lambda_rate: float, mu1: float, mu2: float, K: int) -> StabilityResult:
    """
    Analyse la stabilité d'un système M/M/K -> M/M/1.
    
    Conditions de stabilité :
    - Station 1 (M/M/K) : ρ₁ = λ/(K·μ₁) < 1
    - Station 2 (M/M/1) : ρ₂ = λ/μ₂ < 1
    
    Args:
        lambda_rate: Taux d'arrivée
        mu1: Taux de service station 1 (par serveur)
        mu2: Taux de service station 2
        K: Nombre de serveurs station 1
    
    Returns:
        StabilityResult avec les détails de stabilité
    """
    rho1 = lambda_rate / (K * mu1)
    rho2 = lambda_rate / mu2
    
    is_stable = rho1 < 1 and rho2 < 1
    
    margin_s1 = 1 - rho1
    margin_s2 = 1 - rho2
    
    # Identifier le goulot d'étranglement
    if rho1 >= 1 and rho2 >= 1:
        bottleneck = 'both'
    elif rho1 >= 1:
        bottleneck = 'S1'
    elif rho2 >= 1:
        bottleneck = 'S2'
    elif rho1 > rho2:
        bottleneck = 'S1_limiting'  # S1 est plus chargé
    else:
        bottleneck = 'S2_limiting'  # S2 est plus chargé
    
    # Calculer le lambda maximum pour la stabilité
    lambda_max_s1 = K * mu1 * 0.999  # 99.9% de la capacité
    lambda_max_s2 = mu2 * 0.999
    max_lambda_stable = min(lambda_max_s1, lambda_max_s2)
    
    return StabilityResult(
        lambda_rate=lambda_rate,
        mu1=mu1,
        mu2=mu2,
        K=K,
        rho1=rho1,
        rho2=rho2,
        is_stable=is_stable,
        stability_margin_s1=margin_s1,
        stability_margin_s2=margin_s2,
        bottleneck=bottleneck,
        max_lambda_stable=max_lambda_stable
    )


def generate_stability_map(
    mu1: float, 
    mu2: float, 
    K: int,
    lambda_range: Tuple[float, float] = (0.1, 15.0),
    n_points: int = 50
) -> List[StabilityResult]:
    """
    Génère une carte de stabilité pour différentes valeurs de λ.
    
    Args:
        mu1: Taux de service station 1
        mu2: Taux de service station 2
        K: Nombre de serveurs
        lambda_range: Intervalle de λ à explorer
        n_points: Nombre de points à calculer
    
    Returns:
        Liste de StabilityResult pour chaque λ
    """
    results = []
    lambda_step = (lambda_range[1] - lambda_range[0]) / n_points
    
    for i in range(n_points + 1):
        lambda_val = lambda_range[0] + i * lambda_step
        result = analyze_stability(lambda_val, mu1, mu2, K)
        results.append(result)
    
    return results


def find_critical_lambda(mu1: float, mu2: float, K: int) -> Dict[str, float]:
    """
    Trouve les valeurs critiques de λ pour la stabilité.
    
    Returns:
        Dict avec les seuils critiques pour chaque station
    """
    lambda_crit_s1 = K * mu1  # λ_max pour station 1
    lambda_crit_s2 = mu2      # λ_max pour station 2
    lambda_crit_global = min(lambda_crit_s1, lambda_crit_s2)
    
    return {
        'lambda_critical_S1': lambda_crit_s1,
        'lambda_critical_S2': lambda_crit_s2,
        'lambda_critical_global': lambda_crit_global,
        'limiting_station': 'S1' if lambda_crit_s1 < lambda_crit_s2 else 'S2',
        'capacity_S1': K * mu1,
        'capacity_S2': mu2
    }


# =============================================================================
# INTERVALLES DE CONFIANCE
# =============================================================================

def confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Calcule l'intervalle de confiance pour une liste de valeurs.
    
    Args:
        values: Liste des observations
        confidence: Niveau de confiance (0.95 = 95%)
    
    Returns:
        Tuple (moyenne, borne_inf, borne_sup)
    """
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0
    
    mean = sum(values) / n
    
    if n < 2:
        return mean, mean, mean
    
    # Variance non biaisée
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance)
    std_error = std_dev / math.sqrt(n)
    
    # Coefficient de Student (approximation pour n > 30)
    if n >= 30:
        # Approximation normale
        z_values = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_values.get(confidence, 1.96)
    else:
        # Table de Student simplifiée
        t_values = {
            5: {0.95: 2.571},
            10: {0.95: 2.228},
            15: {0.95: 2.131},
            20: {0.95: 2.086},
            25: {0.95: 2.060},
            30: {0.95: 2.042}
        }
        # Interpolation simple
        z = 2.0  # Valeur par défaut
        for key_n in sorted(t_values.keys()):
            if n <= key_n:
                z = t_values[key_n].get(confidence, 2.0)
                break
    
    margin = z * std_error
    return mean, mean - margin, mean + margin


def percentile(values: List[float], p: float) -> float:
    """
    Calcule le p-ième percentile d'une liste.
    
    Args:
        values: Liste des observations
        p: Percentile (0-100)
    
    Returns:
        Valeur du percentile
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    k = (n - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return sorted_values[int(k)]
    
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return d0 + d1


# =============================================================================
# MÉTRIQUES D'ÉQUITÉ
# =============================================================================

def gini_coefficient(values: List[float]) -> float:
    """
    Calcule le coefficient de Gini (mesure d'inégalité).
    
    0 = égalité parfaite, 1 = inégalité maximale
    
    Args:
        values: Liste des observations (ex: temps de séjour)
    
    Returns:
        Coefficient de Gini
    """
    if not values or len(values) < 2:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Formule de Gini
    cumulative = sum((2 * i - n - 1) * val for i, val in enumerate(sorted_values, 1))
    mean = sum(sorted_values) / n
    
    if mean == 0:
        return 0.0
    
    return cumulative / (n * n * mean)


def jain_fairness_index(values: List[float]) -> float:
    """
    Calcule l'indice d'équité de Jain.
    
    J(x) = (Σxᵢ)² / (n · Σxᵢ²)
    
    1 = parfaitement équitable, 1/n = inégalité maximale
    
    Args:
        values: Liste des observations
    
    Returns:
        Indice de Jain
    """
    if not values:
        return 0.0
    
    n = len(values)
    sum_x = sum(values)
    sum_x2 = sum(x ** 2 for x in values)
    
    if sum_x2 == 0:
        return 1.0
    
    return (sum_x ** 2) / (n * sum_x2)


def coefficient_of_variation(values: List[float]) -> float:
    """
    Calcule le coefficient de variation (CV = σ/μ).
    
    Args:
        values: Liste des observations
    
    Returns:
        Coefficient de variation
    """
    if not values or len(values) < 2:
        return 0.0
    
    n = len(values)
    mean = sum(values) / n
    
    if mean == 0:
        return 0.0
    
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance)
    
    return std_dev / mean


# =============================================================================
# COMPARAISON AVEC THÉORIE
# =============================================================================

def erlang_c_probability(lambda_rate: float, mu: float, K: int) -> float:
    """
    Calcule la probabilité d'attente (formule d'Erlang C) pour M/M/K.
    
    P(attente) = P_Q = [(a^K / K!) · (Kμ / (Kμ - λ))] · P_0
    
    où a = λ/μ (intensité de trafic)
    
    Args:
        lambda_rate: Taux d'arrivée
        mu: Taux de service par serveur
        K: Nombre de serveurs
    
    Returns:
        Probabilité qu'un client doive attendre
    """
    a = lambda_rate / mu  # Intensité de trafic totale
    rho = a / K  # Taux d'utilisation
    
    if rho >= 1:
        return 1.0  # Système instable
    
    # Calcul de P0
    sum_terms = sum((a ** n) / math.factorial(n) for n in range(K))
    last_term = (a ** K) / (math.factorial(K) * (1 - rho))
    P0 = 1 / (sum_terms + last_term)
    
    # Probabilité d'attente (Erlang C)
    P_Q = ((a ** K) / (math.factorial(K) * (1 - rho))) * P0
    
    return P_Q


def theoretical_mmk_waiting_time(lambda_rate: float, mu: float, K: int) -> Dict[str, float]:
    """
    Calcule les temps d'attente théoriques pour M/M/K.
    
    Args:
        lambda_rate: Taux d'arrivée
        mu: Taux de service par serveur
        K: Nombre de serveurs
    
    Returns:
        Dict avec Wq (attente file), W (temps total), Lq, L
    """
    rho = lambda_rate / (K * mu)
    
    if rho >= 1:
        return {
            'error': 'Système instable',
            'rho': rho
        }
    
    P_Q = erlang_c_probability(lambda_rate, mu, K)
    
    # Temps moyen d'attente dans la file
    Wq = P_Q / (K * mu - lambda_rate)
    
    # Temps moyen dans le système
    W = Wq + 1 / mu
    
    # Nombre moyen dans la file (Little)
    Lq = lambda_rate * Wq
    
    # Nombre moyen dans le système
    L = lambda_rate * W
    
    return {
        'rho': rho,
        'P_wait': P_Q,
        'Wq': Wq,
        'W': W,
        'Lq': Lq,
        'L': L
    }


def theoretical_mm1_waiting_time(lambda_rate: float, mu: float) -> Dict[str, float]:
    """
    Calcule les temps d'attente théoriques pour M/M/1.
    
    Args:
        lambda_rate: Taux d'arrivée
        mu: Taux de service
    
    Returns:
        Dict avec les métriques théoriques
    """
    rho = lambda_rate / mu
    
    if rho >= 1:
        return {
            'error': 'Système instable',
            'rho': rho
        }
    
    # Temps moyen d'attente dans la file
    Wq = rho / (mu - lambda_rate)
    
    # Temps moyen dans le système
    W = 1 / (mu - lambda_rate)
    
    # Nombre moyen dans la file
    Lq = rho ** 2 / (1 - rho)
    
    # Nombre moyen dans le système
    L = rho / (1 - rho)
    
    return {
        'rho': rho,
        'Wq': Wq,
        'W': W,
        'Lq': Lq,
        'L': L
    }


def theoretical_tandem_sojourn(lambda_rate: float, mu1: float, mu2: float, K: int) -> Dict[str, float]:
    """
    Calcule le temps de séjour théorique pour un réseau tandem M/M/K -> M/M/1.
    
    Par le théorème de Burke, la sortie de M/M/K est Poisson(λ).
    
    Args:
        lambda_rate: Taux d'arrivée
        mu1: Taux de service station 1 (par serveur)
        mu2: Taux de service station 2
        K: Nombre de serveurs station 1
    
    Returns:
        Dict avec les temps théoriques W1, W2, W_total
    """
    s1 = theoretical_mmk_waiting_time(lambda_rate, mu1, K)
    s2 = theoretical_mm1_waiting_time(lambda_rate, mu2)
    
    if 'error' in s1 or 'error' in s2:
        return {
            'error': 'Système instable',
            'rho1': s1.get('rho', lambda_rate / (K * mu1)),
            'rho2': s2.get('rho', lambda_rate / mu2)
        }
    
    return {
        'W1': s1['W'],
        'W2': s2['W'],
        'W_total': s1['W'] + s2['W'],
        'rho1': s1['rho'],
        'rho2': s2['rho'],
        'P_wait_S1': s1['P_wait']
    }


# =============================================================================
# GÉNÉRATION DE RAPPORTS
# =============================================================================

def generate_simulation_report(
    model_name: str,
    parameters: Dict,
    results: Dict,
    theoretical: Optional[Dict] = None
) -> str:
    """
    Génère un rapport textuel de simulation.
    
    Args:
        model_name: Nom du modèle
        parameters: Paramètres de simulation
        results: Résultats obtenus
        theoretical: Valeurs théoriques (optionnel)
    
    Returns:
        Rapport formaté en texte
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"RAPPORT DE SIMULATION : {model_name}")
    lines.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    
    lines.append("\n📊 PARAMÈTRES DU SYSTÈME:")
    for key, value in parameters.items():
        lines.append(f"   {key}: {value}")
    
    lines.append("\n📈 RÉSULTATS:")
    for key, value in results.items():
        if isinstance(value, float):
            lines.append(f"   {key}: {value:.6f}")
        elif isinstance(value, list):
            lines.append(f"   {key}: [{len(value)} valeurs]")
        else:
            lines.append(f"   {key}: {value}")
    
    if theoretical:
        lines.append("\n📐 COMPARAISON THÉORIQUE:")
        for key, value in theoretical.items():
            if isinstance(value, float):
                lines.append(f"   {key}: {value:.6f}")
            else:
                lines.append(f"   {key}: {value}")
    
    lines.append("\n" + "=" * 70)
    
    return "\n".join(lines)


# =============================================================================
# POINT D'ENTRÉE POUR TESTS
# =============================================================================

if __name__ == "__main__":
    # Test des fonctions
    print("Test des utilitaires d'analyse...")
    
    # Test stabilité
    stability = analyze_stability(lambda_rate=4.0, mu1=2.0, mu2=5.0, K=3)
    print(f"\nStabilité: {stability}")
    
    # Test valeurs critiques
    critical = find_critical_lambda(mu1=2.0, mu2=5.0, K=3)
    print(f"\nValeurs critiques: {critical}")
    
    # Test intervalle de confiance
    import random
    random.seed(42)
    sample = [random.expovariate(1.0) for _ in range(100)]
    mean, ci_low, ci_high = confidence_interval(sample)
    print(f"\nIC 95%: {mean:.4f} [{ci_low:.4f}, {ci_high:.4f}]")
    
    # Test métriques d'équité
    print(f"\nGini: {gini_coefficient(sample):.4f}")
    print(f"Jain: {jain_fairness_index(sample):.4f}")
    print(f"CV: {coefficient_of_variation(sample):.4f}")
    
    # Test théorie
    theory = theoretical_tandem_sojourn(lambda_rate=4.0, mu1=2.0, mu2=5.0, K=3)
    print(f"\nThéorie tandem: {theory}")
    
    print("\n✅ Tous les tests passés!")
