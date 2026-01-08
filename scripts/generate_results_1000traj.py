#!/usr/bin/env python3
"""
Script principal de génération des résultats avec 1000 trajectoires.

Ce script exécute toutes les simulations nécessaires pour le projet ERO2
et génère les données, graphiques et statistiques conformément aux
recommandations du coach (16/12/2025).

Configuration:
- 1000 trajectoires pour des intervalles de confiance robustes
- Warmup de 500 jobs pour atteindre le régime stationnaire
- Exports en CSV/JSON + graphiques PNG

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import os
import sys
import json
import csv
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
from typing import Dict, List, Any, Tuple

# Configuration du style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tandem_queue_simulation import TandemQueueSimulator
from tandem_queue_finite import FiniteQueueSimulator
from tandem_queue_populations import MultiPopulationSimulator, Population
from tandem_queue_backup import BackupQueueSimulator


# =============================================================================
# CONFIGURATION GLOBALE (Recommandations Coach 16/12/2025)
# =============================================================================

CONFIG = {
    'n_trajectories': 1000,        # Nombre de trajectoires pour IC robustes
    'jobs_per_trajectory': 5000,   # Jobs par trajectoire
    'warmup_jobs': 500,            # Warmup pour régime stationnaire
    'confidence_level': 0.95,      # Niveau de confiance pour IC
    'seed': 42,                    # Reproductibilité
    'output_dir': 'data/results_1000traj',
    'img_dir': 'img/generated'
}

# Paramètres du système
SYSTEM_PARAMS = {
    'lambda_rate': 4.0,
    'mu1': 2.0,
    'mu2': 5.0,
    'K': 3,
    'ks': 10,
    'kf': 5
}


def ensure_dirs():
    """Crée les répertoires de sortie."""
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    os.makedirs(CONFIG['img_dir'], exist_ok=True)


def confidence_interval(data: List[float], confidence: float = 0.95) -> Dict:
    """Calcule l'intervalle de confiance."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    se = std / np.sqrt(n)
    
    t_critical = stats.t.ppf((1 + confidence) / 2, df=n-1)
    ci_low = mean - t_critical * se
    ci_high = mean + t_critical * se
    
    return {
        'mean': mean,
        'std': std,
        'variance': np.var(data, ddof=1),
        'se': se,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'half_width': t_critical * se,
        'n': n
    }


# =============================================================================
# SIMULATION 1 : FILES INFINIES (M/M/K → M/M/1)
# =============================================================================

def run_infinite_queue_simulation():
    """Exécute la simulation avec 1000 trajectoires pour files infinies."""
    print("\n" + "="*70)
    print("SIMULATION 1 : FILES INFINIES (M/M/K → M/M/1)")
    print(f"Trajectoires: {CONFIG['n_trajectories']}, Jobs/traj: {CONFIG['jobs_per_trajectory']}")
    print("="*70)
    
    random.seed(CONFIG['seed'])
    np.random.seed(CONFIG['seed'])
    
    lambda_rate = SYSTEM_PARAMS['lambda_rate']
    mu1 = SYSTEM_PARAMS['mu1']
    mu2 = SYSTEM_PARAMS['mu2']
    K = SYSTEM_PARAMS['K']
    
    # Vérification stabilité
    rho1 = lambda_rate / (K * mu1)
    rho2 = lambda_rate / mu2
    print(f"Condition de stabilité: ρ1={rho1:.4f}, ρ2={rho2:.4f}")
    
    if rho1 >= 1 or rho2 >= 1:
        print("⚠️ ERREUR: Système instable!")
        return None
    
    # Stockage des résultats
    trajectory_means = []
    trajectory_vars = []
    all_sojourn_times = []
    
    for i in range(CONFIG['n_trajectories']):
        if (i + 1) % 100 == 0:
            print(f"  Trajectoire {i+1}/{CONFIG['n_trajectories']}...")
        
        sim = TandemQueueSimulator(lambda_rate, mu1, mu2, K)
        sim.run(max_jobs=CONFIG['jobs_per_trajectory'])
        
        # Extraire temps de séjour après warmup
        completed = sim.completed_jobs[CONFIG['warmup_jobs']:]
        sojourn_times = [job.sojourn_time() for job in completed]
        
        if sojourn_times:
            trajectory_means.append(np.mean(sojourn_times))
            trajectory_vars.append(np.var(sojourn_times))
            all_sojourn_times.extend(sojourn_times)
    
    # Calcul des statistiques
    ci = confidence_interval(trajectory_means, CONFIG['confidence_level'])
    
    # Valeurs théoriques
    # E[W1] pour M/M/K (formule Erlang C simplifiée pour ρ < 0.7)
    E_W1_approx = 1 / (K * mu1 - lambda_rate) + 1 / mu1
    E_W2 = 1 / (mu2 - lambda_rate)
    E_W_theoretical = 1 / mu1 + E_W1_approx - 1/mu1 + E_W2  # Approximation
    
    # Pour M/M/K exact, on utilise une formule plus précise
    E_W_theoretical = 0.7222 + 1.0  # Valeurs calculées pour ces paramètres
    
    results = {
        'metadata': {
            'model': 'Infinite Queues (M/M/K → M/M/1)',
            'timestamp': datetime.now().isoformat(),
            'config': CONFIG,
            'system_params': SYSTEM_PARAMS
        },
        'stability': {
            'rho1': rho1,
            'rho2': rho2,
            'stable': True
        },
        'statistics': {
            'mean_sojourn': ci['mean'],
            'variance_sojourn': np.mean(trajectory_vars),
            'std_sojourn': ci['std'],
            'se': ci['se'],
            'ci_95_low': ci['ci_low'],
            'ci_95_high': ci['ci_high'],
            'half_width': ci['half_width'],
            'n_trajectories': ci['n'],
            'total_jobs_analyzed': len(all_sojourn_times)
        },
        'theoretical': {
            'E_W': E_W_theoretical,
            'error_percent': abs(ci['mean'] - E_W_theoretical) / E_W_theoretical * 100
        },
        'trajectory_data': {
            'means': trajectory_means,
            'variances': trajectory_vars
        }
    }
    
    print(f"\n✅ Résultats:")
    print(f"   E[W] = {ci['mean']:.4f} ± {ci['half_width']:.4f} (IC 95%)")
    print(f"   Var[W] = {np.mean(trajectory_vars):.4f}")
    print(f"   Erreur vs théorique: {results['theoretical']['error_percent']:.2f}%")
    
    return results, trajectory_means, all_sojourn_times


# =============================================================================
# SIMULATION 2 : MULTI-POPULATIONS (Superposition)
# =============================================================================

def run_multi_population_simulation():
    """Simule le système avec deux populations (ING + PREPA)."""
    print("\n" + "="*70)
    print("SIMULATION 2 : MULTI-POPULATIONS (Principe de Superposition)")
    print(f"N₁ + N₂ ~ Poisson(λ_ING + λ_PREPA)")
    print("="*70)
    
    random.seed(CONFIG['seed'])
    np.random.seed(CONFIG['seed'])
    
    # Paramètres différenciés
    params = {
        'lambda_ing': 3.0,
        'lambda_prepa': 1.5,
        'mu1_ing': 2.5,
        'mu1_prepa': 1.5,
        'mu2_ing': 5.0,
        'mu2_prepa': 4.0,
        'K': 3,
        'ks': 50,
        'kf': 20
    }
    
    lambda_total = params['lambda_ing'] + params['lambda_prepa']
    print(f"λ_ING = {params['lambda_ing']}, λ_PREPA = {params['lambda_prepa']}")
    print(f"λ_total (superposition) = {lambda_total}")
    
    # Stockage par population
    results_ing = {'sojourn': [], 'waiting': []}
    results_prepa = {'sojourn': [], 'waiting': []}
    
    n_traj = min(200, CONFIG['n_trajectories'])  # Réduit car plus complexe
    
    for i in range(n_traj):
        if (i + 1) % 20 == 0:
            print(f"  Trajectoire {i+1}/{n_traj}...")
        
        sim = MultiPopulationSimulator(**params)
        result = sim.run(max_time=2000.0, warmup_time=200.0)
        
        # Extraire les temps de séjour (déjà filtrés par warmup dans le simulateur)
        # Les clés sont 'ING' et 'PREPA' (strings, pas enums)
        if 'ING' in result and result['ING']['sojourn_times']:
            results_ing['sojourn'].extend(result['ING']['sojourn_times'])
        
        if 'PREPA' in result and result['PREPA']['sojourn_times']:
            results_prepa['sojourn'].extend(result['PREPA']['sojourn_times'])
    
    # Statistiques
    ci_ing = confidence_interval(results_ing['sojourn'])
    ci_prepa = confidence_interval(results_prepa['sojourn'])
    
    results = {
        'metadata': {
            'model': 'Multi-Population (Superposition)',
            'timestamp': datetime.now().isoformat(),
            'params': params
        },
        'superposition': {
            'lambda_total': lambda_total,
            'prop_ing': params['lambda_ing'] / lambda_total,
            'prop_prepa': params['lambda_prepa'] / lambda_total
        },
        'ING': {
            'mean_sojourn': ci_ing['mean'],
            'variance_sojourn': ci_ing['variance'],
            'ci_95': (ci_ing['ci_low'], ci_ing['ci_high']),
            'n_jobs': ci_ing['n']
        },
        'PREPA': {
            'mean_sojourn': ci_prepa['mean'],
            'variance_sojourn': ci_prepa['variance'],
            'ci_95': (ci_prepa['ci_low'], ci_prepa['ci_high']),
            'n_jobs': ci_prepa['n']
        },
        'comparison': {
            'ratio_prepa_ing': ci_prepa['mean'] / ci_ing['mean'],
            'diff_absolute': ci_prepa['mean'] - ci_ing['mean']
        }
    }
    
    print(f"\n✅ Résultats:")
    print(f"   E[W_ING] = {ci_ing['mean']:.4f} ± {ci_ing['half_width']:.4f}")
    print(f"   E[W_PREPA] = {ci_prepa['mean']:.4f} ± {ci_prepa['half_width']:.4f}")
    print(f"   Ratio PREPA/ING: {results['comparison']['ratio_prepa_ing']:.2f}x")
    
    return results, results_ing, results_prepa


# =============================================================================
# GÉNÉRATION DES GRAPHIQUES
# =============================================================================

def generate_graphs(infinite_results, trajectory_means, all_sojourn, 
                    pop_results, results_ing, results_prepa):
    """Génère tous les graphiques pour le rapport."""
    print("\n" + "="*70)
    print("GÉNÉRATION DES GRAPHIQUES")
    print("="*70)
    
    # 1. Distribution des moyennes par trajectoire
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    stats_inf = infinite_results['statistics']
    
    axes[0].hist(trajectory_means, bins=40, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0].axvline(stats_inf['mean_sojourn'], color='red', linewidth=2, 
                    label=f'Moyenne = {stats_inf["mean_sojourn"]:.4f}')
    axes[0].axvline(stats_inf['ci_95_low'], color='green', linestyle='--', 
                    label=f'IC 95%')
    axes[0].axvline(stats_inf['ci_95_high'], color='green', linestyle='--')
    axes[0].set_xlabel('Temps de séjour moyen par trajectoire')
    axes[0].set_ylabel('Fréquence')
    axes[0].set_title(f'Distribution des Moyennes ({CONFIG["n_trajectories"]} trajectoires)')
    axes[0].legend()
    
    # Histogramme des temps individuels
    sample = np.random.choice(all_sojourn, size=min(10000, len(all_sojourn)), replace=False)
    axes[1].hist(sample, bins=50, edgecolor='black', alpha=0.7, density=True, color='coral')
    axes[1].set_xlabel('Temps de séjour')
    axes[1].set_ylabel('Densité')
    axes[1].set_title('Distribution des Temps de Séjour Individuels')
    
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['img_dir'], '01_distribution_trajectoires.png'), dpi=150)
    plt.close()
    print("  ✅ 01_distribution_trajectoires.png")
    
    # 2. Comparaison ING vs PREPA
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Boxplot
    data = [results_ing['sojourn'][:5000], results_prepa['sojourn'][:5000]]
    bp = axes[0].boxplot(data, labels=['ING', 'PREPA'], patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightgreen')
    axes[0].set_ylabel('Temps de séjour')
    axes[0].set_title('Comparaison des Temps de Séjour par Population')
    
    # Histogrammes superposés
    axes[1].hist(results_ing['sojourn'][:5000], bins=50, alpha=0.5, 
                 label=f'ING (μ={pop_results["ING"]["mean_sojourn"]:.2f})', density=True)
    axes[1].hist(results_prepa['sojourn'][:5000], bins=50, alpha=0.5,
                 label=f'PREPA (μ={pop_results["PREPA"]["mean_sojourn"]:.2f})', density=True)
    axes[1].set_xlabel('Temps de séjour')
    axes[1].set_ylabel('Densité')
    axes[1].set_title('Distribution des Temps de Séjour (Superposition)')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['img_dir'], '02_comparaison_populations.png'), dpi=150)
    plt.close()
    print("  ✅ 02_comparaison_populations.png")
    
    # 3. Principe de superposition (démonstration)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    lambda1, lambda2 = 3.0, 1.5
    T = 100
    n_sim = 1000
    
    counts_1 = [np.random.poisson(lambda1 * T) for _ in range(n_sim)]
    counts_2 = [np.random.poisson(lambda2 * T) for _ in range(n_sim)]
    counts_sum = [c1 + c2 for c1, c2 in zip(counts_1, counts_2)]
    
    axes[0].hist(counts_1, bins=30, alpha=0.7, color='blue')
    axes[0].axvline(lambda1*T, color='darkblue', linestyle='--', linewidth=2)
    axes[0].set_title(f'Population ING\nN₁ ~ Poisson({lambda1}×{T})')
    axes[0].set_xlabel('Nombre d\'arrivées')
    
    axes[1].hist(counts_2, bins=30, alpha=0.7, color='green')
    axes[1].axvline(lambda2*T, color='darkgreen', linestyle='--', linewidth=2)
    axes[1].set_title(f'Population PREPA\nN₂ ~ Poisson({lambda2}×{T})')
    axes[1].set_xlabel('Nombre d\'arrivées')
    
    axes[2].hist(counts_sum, bins=30, alpha=0.7, color='red')
    axes[2].axvline((lambda1+lambda2)*T, color='darkred', linestyle='--', linewidth=2)
    axes[2].set_title(f'SUPERPOSITION\nN₁+N₂ ~ Poisson({lambda1+lambda2}×{T})')
    axes[2].set_xlabel('Nombre d\'arrivées')
    
    plt.suptitle('Principe de Superposition des Processus de Poisson', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['img_dir'], '03_superposition_poisson.png'), dpi=150)
    plt.close()
    print("  ✅ 03_superposition_poisson.png")
    
    # 4. Convergence de la moyenne
    fig, ax = plt.subplots(figsize=(12, 6))
    
    cumulative_means = np.cumsum(trajectory_means) / np.arange(1, len(trajectory_means) + 1)
    ax.plot(cumulative_means, 'b-', linewidth=1)
    ax.axhline(stats_inf['mean_sojourn'], color='red', linestyle='--', 
               label=f'Moyenne finale = {stats_inf["mean_sojourn"]:.4f}')
    ax.fill_between(range(len(cumulative_means)), 
                    stats_inf['ci_95_low'], stats_inf['ci_95_high'],
                    alpha=0.2, color='green', label='IC 95%')
    ax.set_xlabel('Nombre de trajectoires')
    ax.set_ylabel('Moyenne cumulative E[W]')
    ax.set_title('Convergence de l\'Estimateur (1000 trajectoires)')
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['img_dir'], '04_convergence_moyenne.png'), dpi=150)
    plt.close()
    print("  ✅ 04_convergence_moyenne.png")
    
    print("\n✅ Tous les graphiques générés!")


# =============================================================================
# EXPORT DES DONNÉES
# =============================================================================

def export_results(infinite_results, trajectory_means, pop_results):
    """Exporte les résultats en CSV et JSON."""
    print("\n" + "="*70)
    print("EXPORT DES DONNÉES")
    print("="*70)
    
    # 1. Export JSON complet
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'config': CONFIG,
            'system_params': SYSTEM_PARAMS,
            'coach_recommendations': {
                'n_trajectories': '1000 (recommandé)',
                'confidence_interval': '95%',
                'superposition_principle': 'N1+N2 ~ Poisson(λ1+λ2)'
            }
        },
        'model1_infinite_queues': infinite_results,
        'model2_multi_populations': pop_results
    }
    
    json_path = os.path.join(CONFIG['output_dir'], 'results_complete.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✅ {json_path}")
    
    # 2. Export CSV des trajectoires
    csv_path = os.path.join(CONFIG['output_dir'], 'trajectories_1000.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['trajectory_id', 'mean_sojourn_time', 'variance'])
        for i, (mean, var) in enumerate(zip(
            trajectory_means, 
            infinite_results['trajectory_data']['variances']
        )):
            writer.writerow([i+1, mean, var])
    print(f"  ✅ {csv_path}")
    
    # 3. Export résumé statistique
    summary_path = os.path.join(CONFIG['output_dir'], 'summary_statistics.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("RÉSUMÉ STATISTIQUE - PROJET ERO2\n")
        f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        f.write("CONFIGURATION:\n")
        f.write(f"  Trajectoires: {CONFIG['n_trajectories']}\n")
        f.write(f"  Jobs/trajectoire: {CONFIG['jobs_per_trajectory']}\n")
        f.write(f"  Warmup: {CONFIG['warmup_jobs']}\n")
        f.write(f"  Niveau de confiance: {CONFIG['confidence_level']*100}%\n\n")
        
        stats = infinite_results['statistics']
        f.write("MODÈLE 1 - FILES INFINIES (M/M/K → M/M/1):\n")
        f.write(f"  E[W] = {stats['mean_sojourn']:.4f}\n")
        f.write(f"  Var[W] = {stats['variance_sojourn']:.4f}\n")
        f.write(f"  IC 95% = [{stats['ci_95_low']:.4f}, {stats['ci_95_high']:.4f}]\n")
        f.write(f"  Demi-largeur IC = ±{stats['half_width']:.4f}\n")
        f.write(f"  Erreur vs théorique = {infinite_results['theoretical']['error_percent']:.2f}%\n\n")
        
        f.write("MODÈLE 2 - MULTI-POPULATIONS:\n")
        f.write(f"  λ_total (superposition) = {pop_results['superposition']['lambda_total']}\n")
        f.write(f"  E[W_ING] = {pop_results['ING']['mean_sojourn']:.4f}\n")
        f.write(f"  E[W_PREPA] = {pop_results['PREPA']['mean_sojourn']:.4f}\n")
        f.write(f"  Ratio PREPA/ING = {pop_results['comparison']['ratio_prepa_ing']:.2f}x\n")
        
    print(f"  ✅ {summary_path}")
    
    print("\n✅ Export terminé!")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Fonction principale."""
    print("\n" + "🚀 "*20)
    print("   GÉNÉRATION DES RÉSULTATS ERO2")
    print("   (1000 trajectoires - Recommandations Coach 16/12/2025)")
    print("🚀 "*20)
    
    ensure_dirs()
    
    # Simulation 1: Files infinies
    infinite_results, trajectory_means, all_sojourn = run_infinite_queue_simulation()
    
    # Simulation 2: Multi-populations
    pop_results, results_ing, results_prepa = run_multi_population_simulation()
    
    # Génération des graphiques
    generate_graphs(infinite_results, trajectory_means, all_sojourn,
                   pop_results, results_ing, results_prepa)
    
    # Export des données
    export_results(infinite_results, trajectory_means, pop_results)
    
    print("\n" + "="*70)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    print("="*70)
    print(f"\nFichiers générés dans:")
    print(f"  - Données: {CONFIG['output_dir']}/")
    print(f"  - Images: {CONFIG['img_dir']}/")
    
    return infinite_results, pop_results


if __name__ == "__main__":
    infinite_results, pop_results = main()
