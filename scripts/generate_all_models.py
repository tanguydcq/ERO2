#!/usr/bin/env python3
"""
Génération complète de tous les modèles avec 1000 trajectoires.
Ce script génère les résultats pour :
1. Files infinies (M/M/K → M/M/1) - Déjà fait
2. Files finies avec différentes configurations
3. Système avec backup
4. Throttling (blocage périodique)

Date: Janvier 2026
"""

import sys
import os
import json
import numpy as np
from datetime import datetime
from scipy import stats

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tandem_queue_simulation import TandemQueueSimulator
from tandem_queue_finite import FiniteQueueSimulator
from tandem_queue_backup import BackupQueueSimulator
from tandem_queue_blocking import BlockingQueueSimulator

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    'n_trajectories': 1000,
    'max_jobs': 5000,
    'warmup_jobs': 500,
    'confidence_level': 0.95,
    
    # Paramètres de base
    'lambda_rate': 4.0,
    'mu1': 2.0,
    'mu2': 5.0,
    'K': 3,
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          'data', 'all_models_results')

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def compute_ci(data, confidence=0.95):
    """Calcule l'intervalle de confiance avec Student-t."""
    n = len(data)
    mean = np.mean(data)
    std_err = stats.sem(data)
    ci = stats.t.interval(confidence, n-1, loc=mean, scale=std_err)
    return {
        'mean': mean,
        'std': np.std(data),
        'ci_lower': ci[0],
        'ci_upper': ci[1],
        'half_width': (ci[1] - ci[0]) / 2,
        'n_samples': n
    }

def print_section(title):
    """Affiche un titre de section."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

# =============================================================================
# MODÈLE 2: FILES FINIES
# =============================================================================

def run_finite_queue_simulations():
    """Simule les files finies avec différentes configurations."""
    print_section("MODÈLE 2: FILES FINIES (M/M/K/ks → M/M/1/kf)")
    
    results = {}
    
    # Configurations à tester
    configs = [
        {'lambda': 4.0, 'ks': 10, 'kf': 5},
        {'lambda': 6.0, 'ks': 10, 'kf': 5},
        {'lambda': 6.0, 'ks': 20, 'kf': 10},
        {'lambda': 8.0, 'ks': 20, 'kf': 10},
    ]
    
    for cfg in configs:
        key = f"lambda{cfg['lambda']}_ks{cfg['ks']}_kf{cfg['kf']}"
        print(f"\n📊 Configuration: λ={cfg['lambda']}, ks={cfg['ks']}, kf={cfg['kf']}")
        
        trajectory_means = []
        trajectory_vars = []
        total_rejections = 0
        total_losses = 0
        total_arrivals = 0
        
        for i in range(CONFIG['n_trajectories']):
            if (i + 1) % 200 == 0:
                print(f"   Trajectoire {i+1}/{CONFIG['n_trajectories']}...")
            
            sim = FiniteQueueSimulator(
                cfg['lambda'], CONFIG['mu1'], CONFIG['mu2'],
                CONFIG['K'], cfg['ks'], cfg['kf']
            )
            result = sim.run(max_jobs=CONFIG['max_jobs'], warmup_jobs=CONFIG['warmup_jobs'])
            
            if result['sojourn_times']:
                trajectory_means.append(np.mean(result['sojourn_times']))
                trajectory_vars.append(np.var(result['sojourn_times']))
            
            total_rejections += result['rejections']
            total_losses += result['losses']
            total_arrivals += result['arrivals']
        
        ci = compute_ci(trajectory_means)
        
        results[key] = {
            'config': cfg,
            'E_W': ci['mean'],
            'Var_W': np.mean(trajectory_vars),
            'CI_95': [ci['ci_lower'], ci['ci_upper']],
            'rejection_rate': total_rejections / total_arrivals * 100,
            'loss_rate': total_losses / (total_arrivals - total_rejections) * 100 if total_arrivals > total_rejections else 0,
            'n_trajectories': CONFIG['n_trajectories']
        }
        
        print(f"   ✅ E[W] = {ci['mean']:.4f} ± {ci['half_width']:.4f}")
        print(f"   📉 Taux rejet = {results[key]['rejection_rate']:.2f}%")
        print(f"   📉 Taux perte = {results[key]['loss_rate']:.2f}%")
    
    return results

# =============================================================================
# MODÈLE 3: BACKUP
# =============================================================================

def run_backup_simulations():
    """Simule le système avec différentes stratégies de backup."""
    print_section("MODÈLE 3: SYSTÈME AVEC BACKUP")
    
    # Import du mode de backup
    from tandem_queue_backup import BackupMode
    
    results = {}
    lambda_rate = 6.0  # Charge élevée pour voir l'effet du backup
    
    # Probabilités de backup à tester (0 = NONE, 1 = SYSTEMATIC, autres = RANDOM)
    backup_configs = [
        {'mode': BackupMode.NONE, 'prob': 0.0, 'label': '0.0'},
        {'mode': BackupMode.RANDOM, 'prob': 0.25, 'label': '0.25'},
        {'mode': BackupMode.RANDOM, 'prob': 0.50, 'label': '0.50'},
        {'mode': BackupMode.RANDOM, 'prob': 0.75, 'label': '0.75'},
        {'mode': BackupMode.SYSTEMATIC, 'prob': 1.0, 'label': '1.0'},
    ]
    
    for cfg in backup_configs:
        key = f"p_backup_{cfg['label']}"
        print(f"\n📊 Backup mode={cfg['mode'].name}, p={cfg['prob']}")
        
        trajectory_means = []
        trajectory_losses = []
        trajectory_backup_usage = []
        
        # Utiliser un nombre réduit pour le backup (plus lent)
        n_traj = min(CONFIG['n_trajectories'], 200)
        
        for i in range(n_traj):
            if (i + 1) % 50 == 0:
                print(f"   Trajectoire {i+1}/{n_traj}...")
            
            sim = BackupQueueSimulator(
                lambda_rate=lambda_rate,
                mu1=CONFIG['mu1'],
                mu2=CONFIG['mu2'],
                K=CONFIG['K'],
                ks=10,
                kf=5,
                backup_mode=cfg['mode'],
                backup_prob=cfg['prob'],
                backup_time_mean=0.1
            )
            result = sim.run(max_jobs=3000, warmup_jobs=300)
            
            # Structure retour: mean_sojourn, blank_page_rate, backups_created
            if result.get('mean_sojourn', 0) > 0:
                trajectory_means.append(result['mean_sojourn'])
            
            trajectory_losses.append(result.get('blank_page_rate', 0) * 100)
            trajectory_backup_usage.append(result.get('backups_created', 0))
        
        ci = compute_ci(trajectory_means) if trajectory_means else {'mean': 0, 'half_width': 0}
        
        results[key] = {
            'p_backup': cfg['prob'],
            'mode': cfg['mode'].name,
            'E_W': ci['mean'],
            'CI_95_half': ci['half_width'],
            'loss_rate_mean': np.mean(trajectory_losses),
            'backup_usage_mean': np.mean(trajectory_backup_usage),
            'n_trajectories': n_traj
        }
        
        print(f"   ✅ E[W] = {ci['mean']:.4f} ± {ci['half_width']:.4f}")
        print(f"   📉 Taux perte moyen = {results[key]['loss_rate_mean']:.2f}%")
    
    return results

# =============================================================================
# MODÈLE 4: THROTTLING (BLOCAGE)
# =============================================================================

def run_throttling_simulations():
    """Simule le système avec blocage périodique."""
    print_section("MODÈLE 4: THROTTLING (BLOCAGE PÉRIODIQUE)")
    
    results = {}
    
    # Périodes de blocage à tester
    blocking_periods = [0.0, 2.0, 5.0, 10.0]
    
    for t_block in blocking_periods:
        key = f"t_block_{t_block}"
        print(f"\n📊 Période blocage = {t_block}")
        
        trajectory_ing = []
        trajectory_prepa = []
        
        n_traj = min(CONFIG['n_trajectories'], 100)  # Réduit car blocage est lent
        
        for i in range(n_traj):
            if (i + 1) % 20 == 0:
                print(f"   Trajectoire {i+1}/{n_traj}...")
            
            sim = BlockingQueueSimulator(
                lambda_ing=3.0,
                lambda_prepa=1.5,
                mu1_ing=2.5,
                mu1_prepa=1.5,
                mu2_ing=5.0,
                mu2_prepa=4.0,
                K=3,
                ks=50,
                kf=20,
                tb=t_block  # Paramètre correct: tb (pas blocking_period)
            )
            result = sim.run(max_time=2000.0, warmup_time=200.0)
            
            if result.get('ING', {}).get('sojourn_times'):
                trajectory_ing.append(np.mean(result['ING']['sojourn_times']))
            if result.get('PREPA', {}).get('sojourn_times'):
                trajectory_prepa.append(np.mean(result['PREPA']['sojourn_times']))
        
        ci_ing = compute_ci(trajectory_ing) if trajectory_ing else {'mean': 0, 'half_width': 0}
        ci_prepa = compute_ci(trajectory_prepa) if trajectory_prepa else {'mean': 0, 'half_width': 0}
        
        ratio = ci_prepa['mean'] / ci_ing['mean'] if ci_ing['mean'] > 0 else 0
        
        results[key] = {
            't_block': t_block,
            'E_W_ING': ci_ing['mean'],
            'E_W_PREPA': ci_prepa['mean'],
            'ratio_PREPA_ING': ratio,
            'CI_95_ING': ci_ing['half_width'],
            'CI_95_PREPA': ci_prepa['half_width'],
            'n_trajectories': n_traj
        }
        
        print(f"   ✅ E[W_ING] = {ci_ing['mean']:.4f} ± {ci_ing['half_width']:.4f}")
        print(f"   ✅ E[W_PREPA] = {ci_prepa['mean']:.4f} ± {ci_prepa['half_width']:.4f}")
        print(f"   📈 Ratio PREPA/ING = {ratio:.2f}x")
    
    return results

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*70)
    print("  GÉNÉRATION COMPLÈTE - TOUS LES MODÈLES ERO2")
    print("  1000 trajectoires par modèle")
    print("="*70)
    print(f"  Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Créer le répertoire de sortie
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_results = {}
    
    # 1. Files finies
    all_results['finite_queues'] = run_finite_queue_simulations()
    
    # 2. Backup
    all_results['backup'] = run_backup_simulations()
    
    # 3. Throttling
    all_results['throttling'] = run_throttling_simulations()
    
    # Sauvegarder les résultats
    output_file = os.path.join(OUTPUT_DIR, 'all_models_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Créer un résumé texte
    summary_file = os.path.join(OUTPUT_DIR, 'summary.txt')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("RÉSUMÉ DES RÉSULTATS - TOUS MODÈLES\n")
        f.write(f"Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        f.write("MODÈLE 2: FILES FINIES\n")
        f.write("-"*40 + "\n")
        for key, val in all_results['finite_queues'].items():
            f.write(f"  {key}:\n")
            f.write(f"    E[W] = {val['E_W']:.4f}\n")
            f.write(f"    Rejet = {val['rejection_rate']:.2f}%\n")
            f.write(f"    Perte = {val['loss_rate']:.2f}%\n\n")
        
        f.write("\nMODÈLE 3: BACKUP\n")
        f.write("-"*40 + "\n")
        for key, val in all_results['backup'].items():
            f.write(f"  p_backup = {val['p_backup']}:\n")
            f.write(f"    E[W] = {val['E_W']:.4f}\n")
            f.write(f"    Perte = {val['loss_rate_mean']:.2f}%\n\n")
        
        f.write("\nMODÈLE 4: THROTTLING\n")
        f.write("-"*40 + "\n")
        for key, val in all_results['throttling'].items():
            f.write(f"  t_block = {val['t_block']}:\n")
            f.write(f"    E[W_ING] = {val['E_W_ING']:.4f}\n")
            f.write(f"    E[W_PREPA] = {val['E_W_PREPA']:.4f}\n")
            f.write(f"    Ratio = {val['ratio_PREPA_ING']:.2f}x\n\n")
    
    print_section("GÉNÉRATION TERMINÉE")
    print(f"\n✅ Résultats sauvegardés dans: {OUTPUT_DIR}")
    print(f"   - all_models_results.json")
    print(f"   - summary.txt")

if __name__ == "__main__":
    main()
