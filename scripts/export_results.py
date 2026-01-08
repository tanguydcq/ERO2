#!/usr/bin/env python3
"""
Script d'export des résultats de simulation en données brutes.

Ce script exécute toutes les simulations et exporte les résultats dans :
- Fichiers CSV pour les données tabulaires
- Fichiers JSON pour les métadonnées et résultats structurés

Les données exportées permettent de :
- Reproduire les analyses
- Vérifier les résultats
- Générer des graphiques personnalisés

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import os
import sys
import json
import csv
import random
from datetime import datetime
from typing import Dict, List, Any

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des simulateurs
from tandem_queue_simulation import TandemQueueSimulator, run_multiple_simulations
from tandem_queue_finite import FiniteQueueSimulator, run_parameter_study
from tandem_queue_populations import MultiPopulationSimulator
from tandem_queue_blocking import BlockingQueueSimulator
from tandem_queue_priority import PriorityQueueSimulator, PriorityPolicy, compare_policies

# Import des utilitaires
from utils.analysis_utils import (
    export_to_csv, export_to_json, analyze_stability, 
    find_critical_lambda, theoretical_tandem_sojourn,
    confidence_interval, gini_coefficient, jain_fairness_index
)


# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = "data/raw_results"
SEED = 42


def ensure_output_dir():
    """Crée le répertoire de sortie si nécessaire."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# EXPORT MODÈLE 1 : FILES INFINIES
# =============================================================================

def export_infinite_queue_results():
    """Exporte les résultats du modèle à files infinies."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE 1 : FILES INFINIES (M/M/K → M/M/1)")
    print("="*60)
    
    random.seed(SEED)
    
    # Paramètres (1000 trajectoires pour IC robustes - recommandation coach 16/12/2025)
    params = {
        'lambda_rate': 4.0,
        'mu1': 2.0,
        'mu2': 5.0,
        'K': 3,
        'n_trajectories': 1000,  # Augmenté de 30 à 1000 pour intervalles de confiance fiables
        'jobs_per_trajectory': 5000,
        'warmup_jobs': 500
    }
    
    # Exécuter la simulation
    results = run_multiple_simulations(**params, seed=SEED)
    
    # Préparer les données pour export
    trajectory_data = []
    for i, (mean, var) in enumerate(zip(
        results['trajectory_stats']['means'],
        results['trajectory_stats']['variances']
    )):
        trajectory_data.append({
            'trajectory_id': i + 1,
            'mean_sojourn_time': mean,
            'variance_sojourn_time': var
        })
    
    # Export CSV des trajectoires
    csv_path = os.path.join(OUTPUT_DIR, "model1_infinite_trajectories.csv")
    export_to_csv(trajectory_data, csv_path)
    print(f"✅ Trajectoires exportées : {csv_path}")
    
    # Calcul des valeurs théoriques
    theoretical = theoretical_tandem_sojourn(
        params['lambda_rate'], params['mu1'], params['mu2'], params['K']
    )
    
    # Analyse de stabilité
    stability = analyze_stability(
        params['lambda_rate'], params['mu1'], params['mu2'], params['K']
    )
    
    # Export JSON complet
    full_results = {
        'metadata': {
            'model': 'Infinite Queues (M/M/K → M/M/1)',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'parameters': params,
        'simulation_results': {
            'mean_sojourn_time': results['sojourn_time']['mean'],
            'variance_sojourn_time': results['sojourn_time']['variance'],
            'std_dev': results['sojourn_time']['std_dev'],
            'std_error': results['sojourn_time']['std_error'],
            'ci_95_lower': results['sojourn_time']['ci_95_lower'],
            'ci_95_upper': results['sojourn_time']['ci_95_upper'],
            'total_jobs_analyzed': results['simulation']['total_jobs_analyzed']
        },
        'theoretical_values': theoretical,
        'stability_analysis': stability.to_dict(),
        'trajectory_means': results['trajectory_stats']['means'],
        'trajectory_variances': results['trajectory_stats']['variances']
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model1_infinite_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT MODÈLE 2 : CAPACITÉS FINIES
# =============================================================================

def export_finite_queue_results():
    """Exporte les résultats du modèle à capacités finies."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE 2 : CAPACITÉS FINIES (M/M/K/ks → M/M/1/kf)")
    print("="*60)
    
    random.seed(SEED)
    
    # Paramètres
    params = {
        'mu1': 2.0,
        'mu2': 5.0,
        'K': 3,
        'ks': 10,
        'kf': 5,
        'n_trajectories': 15,
        'jobs_per_traj': 10000,
        'warmup': 1000
    }
    
    lambda_values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    # Exécuter l'étude paramétrique
    results = run_parameter_study(
        lambda_values=lambda_values,
        **{k: v for k, v in params.items() if k not in ['n_trajectories', 'jobs_per_traj', 'warmup']},
        n_trajectories=params['n_trajectories'],
        jobs_per_traj=params['jobs_per_traj'],
        warmup=params['warmup'],
        seed=SEED
    )
    
    # Préparer les données pour export CSV
    csv_data = []
    for i, lam in enumerate(lambda_values):
        csv_data.append({
            'lambda': lam,
            'rejection_rate_mean': results['rejection_rate_mean'][i],
            'rejection_rate_std': results['rejection_rate_std'][i],
            'loss_rate_mean': results['loss_rate_mean'][i],
            'loss_rate_std': results['loss_rate_std'][i],
            'sojourn_mean': results['sojourn_mean'][i],
            'sojourn_std': results['sojourn_std'][i],
            'throughput_mean': results['throughput_mean'][i],
            'throughput_std': results['throughput_std'][i]
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model2_finite_parametric.csv")
    export_to_csv(csv_data, csv_path)
    print(f"✅ Étude paramétrique exportée : {csv_path}")
    
    # Étude des capacités
    capacity_configs = [(5, 3), (10, 5), (20, 10), (50, 20)]
    capacity_results = []
    
    for ks, kf in capacity_configs:
        print(f"   Testing ks={ks}, kf={kf}...")
        for lam in [4.0, 6.0, 8.0]:
            sim = FiniteQueueSimulator(lam, params['mu1'], params['mu2'], params['K'], ks, kf)
            res = sim.run(max_jobs=5000, warmup_jobs=500)
            capacity_results.append({
                'ks': ks,
                'kf': kf,
                'lambda': lam,
                'rejection_rate': res['rejection_rate'],
                'loss_rate': res['loss_rate'],
                'mean_sojourn': res['mean_sojourn'],
                'throughput': res['throughput']
            })
    
    csv_path = os.path.join(OUTPUT_DIR, "model2_capacity_study.csv")
    export_to_csv(capacity_results, csv_path)
    print(f"✅ Étude des capacités exportée : {csv_path}")
    
    # Export JSON complet
    critical = find_critical_lambda(params['mu1'], params['mu2'], params['K'])
    
    full_results = {
        'metadata': {
            'model': 'Finite Queues (M/M/K/ks → M/M/1/kf)',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'parameters': params,
        'parametric_study': csv_data,
        'capacity_study': capacity_results,
        'critical_values': critical
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model2_finite_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT MODÈLE 3 : BACKUP
# =============================================================================

def export_backup_results():
    """Exporte les résultats du modèle avec backup."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE 3 : MÉCANISME DE BACKUP")
    print("="*60)
    
    random.seed(SEED)
    
    from tandem_queue_backup import BackupQueueSimulator, BackupMode
    
    params = {
        'lambda_rate': 6.0,
        'mu1': 2.0,
        'mu2': 5.0,
        'K': 3,
        'ks': 10,
        'kf': 5
    }
    
    backup_modes = [
        ('NONE', BackupMode.NONE, 0.0),
        ('RANDOM_25', BackupMode.RANDOM, 0.25),
        ('RANDOM_50', BackupMode.RANDOM, 0.50),
        ('RANDOM_75', BackupMode.RANDOM, 0.75),
        ('SYSTEMATIC', BackupMode.SYSTEMATIC, 1.0)
    ]
    
    results = []
    n_trajectories = 15
    
    for name, mode, prob in backup_modes:
        print(f"   Testing {name}...")
        
        losses_list = []
        sojourn_list = []
        storage_list = []
        
        for _ in range(n_trajectories):
            sim = BackupQueueSimulator(
                lambda_rate=params['lambda_rate'],
                mu1=params['mu1'],
                mu2=params['mu2'],
                K=params['K'],
                ks=params['ks'],
                kf=params['kf'],
                backup_mode=mode,
                backup_prob=prob
            )
            res = sim.run(max_jobs=10000, warmup_jobs=1000)
            
            losses_list.append(res.get('blank_page_rate', 0))
            sojourn_list.append(res.get('mean_sojourn', 0))
            storage_list.append(res.get('total_backups', 0))
        
        results.append({
            'mode': name,
            'backup_prob': prob,
            'blank_page_rate_mean': sum(losses_list) / len(losses_list),
            'blank_page_rate_std': (sum((x - sum(losses_list)/len(losses_list))**2 for x in losses_list) / len(losses_list))**0.5,
            'mean_sojourn_mean': sum(sojourn_list) / len(sojourn_list) if sojourn_list else 0,
            'storage_used_mean': sum(storage_list) / len(storage_list)
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model3_backup_comparison.csv")
    export_to_csv(results, csv_path)
    print(f"✅ Comparaison backup exportée : {csv_path}")
    
    # Export JSON
    full_results = {
        'metadata': {
            'model': 'Backup Mechanism',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'parameters': params,
        'backup_comparison': results
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model3_backup_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT MODÈLE 4 : MULTI-POPULATIONS
# =============================================================================

def export_population_results():
    """Exporte les résultats du modèle multi-populations."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE 4 : MULTI-POPULATIONS (ING vs PREPA)")
    print("="*60)
    
    random.seed(SEED)
    
    params = {
        'lambda_ing': 3.0,
        'lambda_prepa': 1.0,
        'mu1_ing': 4.0,
        'mu1_prepa': 1.0,
        'mu2_ing': 8.0,
        'mu2_prepa': 3.0,
        'K': 3
    }
    
    n_trajectories = 20
    results = []
    
    for _ in range(n_trajectories):
        sim = MultiPopulationSimulator(**params)
        res = sim.run(max_jobs=10000, warmup_jobs=1000)
        
        results.append({
            'trajectory': len(results) + 1,
            'E_W_ING': res['populations']['ING']['mean_sojourn'],
            'E_W_PREPA': res['populations']['PREPA']['mean_sojourn'],
            'completions_ING': res['populations']['ING']['completions'],
            'completions_PREPA': res['populations']['PREPA']['completions']
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model4_populations_trajectories.csv")
    export_to_csv(results, csv_path)
    print(f"✅ Trajectoires exportées : {csv_path}")
    
    # Étude du ratio ING/PREPA
    ratio_study = []
    for ing_prop in [0.1, 0.3, 0.5, 0.7, 0.9]:
        lambda_total = 4.0
        lambda_ing = lambda_total * ing_prop
        lambda_prepa = lambda_total * (1 - ing_prop)
        
        sim = MultiPopulationSimulator(
            lambda_ing=lambda_ing,
            lambda_prepa=lambda_prepa,
            mu1_ing=params['mu1_ing'],
            mu1_prepa=params['mu1_prepa'],
            mu2_ing=params['mu2_ing'],
            mu2_prepa=params['mu2_prepa'],
            K=params['K']
        )
        res = sim.run(max_jobs=10000, warmup_jobs=1000)
        
        ratio_study.append({
            'ing_proportion': ing_prop,
            'lambda_ing': lambda_ing,
            'lambda_prepa': lambda_prepa,
            'E_W_ING': res['populations']['ING']['mean_sojourn'],
            'E_W_PREPA': res['populations']['PREPA']['mean_sojourn']
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model4_ratio_study.csv")
    export_to_csv(ratio_study, csv_path)
    print(f"✅ Étude des ratios exportée : {csv_path}")
    
    # Export JSON
    full_results = {
        'metadata': {
            'model': 'Multi-Population (ING vs PREPA)',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'parameters': params,
        'trajectories': results,
        'ratio_study': ratio_study
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model4_populations_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT MODÈLE 5 : BLOCAGE PÉRIODIQUE
# =============================================================================

def export_blocking_results():
    """Exporte les résultats du modèle avec blocage."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE 5 : BLOCAGE PÉRIODIQUE")
    print("="*60)
    
    random.seed(SEED)
    
    params = {
        'lambda_ing': 3.0,
        'lambda_prepa': 1.0,
        'mu1_ing': 4.0,
        'mu1_prepa': 1.0,
        'mu2_ing': 8.0,
        'mu2_prepa': 3.0,
        'K': 3
    }
    
    tb_values = [0.0, 1.0, 2.0, 5.0, 10.0]
    results = []
    
    for tb in tb_values:
        print(f"   Testing tb={tb}...")
        
        sim = BlockingQueueSimulator(
            **params,
            tb=tb
        )
        res = sim.run(max_jobs=10000, warmup_jobs=1000)
        
        results.append({
            'tb': tb,
            'availability': 0.5 / 1.5 if tb > 0 else 1.0,
            'E_W_ING': res['populations']['ING']['mean_sojourn'],
            'E_W_PREPA': res['populations']['PREPA']['mean_sojourn'],
            'ratio_PREPA_ING': res['populations']['PREPA']['mean_sojourn'] / res['populations']['ING']['mean_sojourn'] if res['populations']['ING']['mean_sojourn'] > 0 else 0
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model5_blocking_study.csv")
    export_to_csv(results, csv_path)
    print(f"✅ Étude du blocage exportée : {csv_path}")
    
    # Export JSON
    full_results = {
        'metadata': {
            'model': 'Periodic Blocking',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'parameters': params,
        'blocking_study': results
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model5_blocking_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT MODÈLE ALTERNATIF : PRIORITÉS
# =============================================================================

def export_priority_results():
    """Exporte les résultats du modèle avec priorités."""
    print("\n" + "="*60)
    print("EXPORT MODÈLE ALTERNATIF : POLITIQUES DE PRIORITÉ")
    print("="*60)
    
    random.seed(SEED)
    
    # Comparer les politiques
    results = compare_policies(
        lambda_ing=3.0,
        lambda_prepa=1.0,
        mu1_ing=4.0,
        mu1_prepa=1.0,
        mu2_ing=8.0,
        mu2_prepa=3.0,
        K=3,
        n_trajectories=15,
        jobs_per_traj=10000,
        warmup=1000,
        seed=SEED
    )
    
    # Préparer pour CSV
    csv_data = []
    for policy, data in results.items():
        csv_data.append({
            'policy': policy,
            'E_W_ING': data['E[W]_ING'],
            'std_ING': data['std_ING'],
            'E_W_PREPA': data['E[W]_PREPA'],
            'std_PREPA': data['std_PREPA'],
            'E_W_global': data['E[W]_global'],
            'std_global': data['std_global'],
            'ratio_PREPA_ING': data['ratio_PREPA_ING']
        })
    
    csv_path = os.path.join(OUTPUT_DIR, "model_priority_comparison.csv")
    export_to_csv(csv_data, csv_path)
    print(f"✅ Comparaison des politiques exportée : {csv_path}")
    
    # Export JSON
    full_results = {
        'metadata': {
            'model': 'Priority Policies',
            'timestamp': datetime.now().isoformat(),
            'seed': SEED
        },
        'policy_comparison': results
    }
    
    json_path = os.path.join(OUTPUT_DIR, "model_priority_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Résultats complets exportés : {json_path}")
    
    return full_results


# =============================================================================
# EXPORT ANALYSE DE STABILITÉ
# =============================================================================

def export_stability_analysis():
    """Exporte l'analyse de stabilité complète."""
    print("\n" + "="*60)
    print("EXPORT ANALYSE DE STABILITÉ")
    print("="*60)
    
    # Paramètres de base
    mu1, mu2, K = 2.0, 5.0, 3
    
    # Générer la carte de stabilité
    from utils.analysis_utils import generate_stability_map
    
    stability_map = generate_stability_map(
        mu1=mu1, mu2=mu2, K=K,
        lambda_range=(0.1, 12.0),
        n_points=60
    )
    
    # Export CSV
    csv_data = [s.to_dict() for s in stability_map]
    csv_path = os.path.join(OUTPUT_DIR, "stability_map.csv")
    export_to_csv(csv_data, csv_path)
    print(f"✅ Carte de stabilité exportée : {csv_path}")
    
    # Valeurs critiques
    critical = find_critical_lambda(mu1, mu2, K)
    
    # Export JSON
    full_results = {
        'metadata': {
            'analysis': 'Stability Analysis',
            'timestamp': datetime.now().isoformat()
        },
        'parameters': {'mu1': mu1, 'mu2': mu2, 'K': K},
        'critical_values': critical,
        'stability_map': csv_data
    }
    
    json_path = os.path.join(OUTPUT_DIR, "stability_analysis_full.json")
    export_to_json(full_results, json_path)
    print(f"✅ Analyse complète exportée : {json_path}")
    
    return full_results


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Exporte tous les résultats."""
    print("\n" + "🚀 " * 20)
    print("   EXPORT COMPLET DES RÉSULTATS DE SIMULATION")
    print("🚀 " * 20)
    
    ensure_output_dir()
    
    # Export de chaque modèle
    results = {}
    
    try:
        results['infinite'] = export_infinite_queue_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle 1: {e}")
    
    try:
        results['finite'] = export_finite_queue_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle 2: {e}")
    
    try:
        results['backup'] = export_backup_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle 3: {e}")
    
    try:
        results['populations'] = export_population_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle 4: {e}")
    
    try:
        results['blocking'] = export_blocking_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle 5: {e}")
    
    try:
        results['priority'] = export_priority_results()
    except Exception as e:
        print(f"⚠️  Erreur modèle priorité: {e}")
    
    try:
        results['stability'] = export_stability_analysis()
    except Exception as e:
        print(f"⚠️  Erreur stabilité: {e}")
    
    # Résumé final
    print("\n" + "="*60)
    print("EXPORT TERMINÉ")
    print("="*60)
    print(f"Répertoire de sortie : {os.path.abspath(OUTPUT_DIR)}")
    print(f"Fichiers générés :")
    for f in os.listdir(OUTPUT_DIR):
        filepath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(filepath)
        print(f"   • {f} ({size:,} bytes)")
    
    return results


if __name__ == "__main__":
    main()
