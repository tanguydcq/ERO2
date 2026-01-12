#!/usr/bin/env python3
"""
Dashboard Streamlit pour la visualisation des simulations ERO2.
Usage: streamlit run dashboard.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import sys
import os

# Import des simulateurs
from tandem_queue_simulation import TandemQueueSimulator
from tandem_queue_finite import FiniteQueueSimulator
from tandem_queue_backup import BackupQueueSimulator, BackupMode
from tandem_queue_populations import MultiPopulationSimulator
from tandem_queue_blocking import BlockingQueueSimulator

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(page_title="ERO2 - Files d'attente", layout="wide")

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def compute_stats(values: List[float]) -> Dict[str, float]:
    """Calcule les statistiques descriptives."""
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}
    arr = np.array(values)
    return {
        "mean": np.mean(arr),
        "std": np.std(arr),
        "min": np.min(arr),
        "max": np.max(arr),
        "median": np.median(arr)
    }

def stability_indicator(rho: float) -> str:
    """Retourne un indicateur de stabilité."""
    if rho < 0.7:
        return "🟢"
    elif rho < 0.9:
        return "🟡"
    elif rho < 1.0:
        return "🟠"
    else:
        return "🔴"

# =============================================================================
# SIDEBAR - PARAMÈTRES
# =============================================================================

st.sidebar.title("⚙️ Paramètres")

model = st.sidebar.selectbox(
    "Modèle",
    ["Waterfall (Infini)", "Files Finies", "Backup", "Populations", "Throttling"]
)

st.sidebar.markdown("---")

# Paramètres communs
lambda_rate = st.sidebar.slider("λ (taux d'arrivée)", 0.5, 10.0, 4.0, 0.5)
mu1 = st.sidebar.slider("μ₁ (service S1)", 0.5, 10.0, 2.0, 0.5)
mu2 = st.sidebar.slider("μ₂ (service S2)", 0.5, 15.0, 5.0, 0.5)
K = st.sidebar.slider("K (serveurs S1)", 1, 10, 3)

# Initialisation par défaut
ks = 0
kf = 0

# Paramètres spécifiques selon le modèle
if model == "Files Finies":
    st.sidebar.markdown("---")
    ks = st.sidebar.slider("kₛ (capacité S1)", K, 50, 15)
    kf = st.sidebar.slider("kf (capacité S2)", 1, 50, 10)

elif model == "Backup":
    st.sidebar.markdown("---")
    ks = st.sidebar.slider("kₛ (capacité S1)", K, 50, 15)
    kf = st.sidebar.slider("kf (capacité S2)", 1, 50, 10)
    backup_mode = st.sidebar.selectbox("Mode backup", ["Aucun", "Systématique", "Aléatoire"])
    if backup_mode == "Aléatoire":
        backup_prob = st.sidebar.slider("Probabilité backup", 0.0, 1.0, 0.5, 0.1)
    else:
        backup_prob = 1.0
    backup_time = st.sidebar.slider("Temps backup", 0.01, 1.0, 0.1, 0.01)

elif model == "Populations":
    st.sidebar.markdown("---")
    lambda_ing = st.sidebar.slider("λ_ING", 0.5, 10.0, 3.0, 0.5)
    lambda_prepa = st.sidebar.slider("λ_PREPA", 0.1, 5.0, 1.0, 0.1)
    mu1_ing = st.sidebar.slider("μ₁ ING (rapide)", 1.0, 10.0, 3.0, 0.5)
    mu1_prepa = st.sidebar.slider("μ₁ PREPA (lent)", 0.5, 5.0, 1.0, 0.5)
    lambda_rate = lambda_ing + lambda_prepa  # Pour calcul rho

elif model == "Throttling":
    st.sidebar.markdown("---")
    lambda_ing = st.sidebar.slider("λ_ING", 0.5, 10.0, 3.0, 0.5)
    lambda_prepa = st.sidebar.slider("λ_PREPA", 0.1, 5.0, 1.0, 0.1)
    mu1_ing = st.sidebar.slider("μ₁ ING", 1.0, 10.0, 3.0, 0.5)
    mu1_prepa = st.sidebar.slider("μ₁ PREPA", 0.5, 5.0, 1.0, 0.5)
    t_block = st.sidebar.slider("t_block (durée blocage)", 0.5, 10.0, 2.0, 0.5)
    lambda_rate = lambda_ing + lambda_prepa

st.sidebar.markdown("---")
n_jobs = st.sidebar.slider("Jobs à simuler", 500, 10000, 2000, 500)
warmup = st.sidebar.slider("Warmup", 100, 2000, 500, 100)
n_runs = st.sidebar.slider("Trajectoires", 1, 50, 10)

# Paramètres de coût
st.sidebar.markdown("---")
st.sidebar.markdown("**💰 Coûts unitaires**")
cost_sojourn = st.sidebar.number_input("Coût/unité temps séjour", 0.0, 100.0, 1.0, 0.1)
cost_reject = st.sidebar.number_input("Coût/rejet", 0.0, 100.0, 10.0, 1.0)
cost_loss = st.sidebar.number_input("Coût/page blanche", 0.0, 100.0, 20.0, 1.0)
cost_server = st.sidebar.number_input("Coût/serveur", 0.0, 50.0, 5.0, 0.5)
cost_capacity = st.sidebar.number_input("Coût/unité capacité", 0.0, 10.0, 0.5, 0.1)

# =============================================================================
# HEADER
# =============================================================================

st.title("📊 ERO2 - Analyse des Systèmes d'Attente")

# Indicateurs de stabilité
col1, col2, col3 = st.columns(3)
rho1 = lambda_rate / (K * mu1)
rho2 = lambda_rate / mu2

with col1:
    st.metric("ρ₁ (Station 1)", f"{rho1:.3f}", delta=None)
    st.caption(f"{stability_indicator(rho1)} {'Stable' if rho1 < 1 else 'Instable'}")
with col2:
    st.metric("ρ₂ (Station 2)", f"{rho2:.3f}", delta=None)
    st.caption(f"{stability_indicator(rho2)} {'Stable' if rho2 < 1 else 'Instable'}")
with col3:
    st.metric("ρ_max", f"{max(rho1, rho2):.3f}", delta=None)
    bottleneck = "S1" if rho1 > rho2 else "S2"
    st.caption(f"Goulot: {bottleneck}")

st.markdown("---")

# =============================================================================
# ONGLETS PRINCIPAUX
# =============================================================================

main_tab1, main_tab2 = st.tabs(["🎮 Simulation", "📈 Étude Paramétrique"])

with main_tab1:
    run_button = st.button("▶️ Lancer simulation", type="primary")

    # =============================================================================
    # SIMULATION
    # =============================================================================

    if run_button:
        progress = st.progress(0, text="Simulation en cours...")
        
        all_sojourn = []
        all_wait_s1 = []
        all_wait_s2 = []
        all_rejected = []
        all_lost = []
        
        # Variables spécifiques populations
        sojourn_ing = []
        sojourn_prepa = []
        
        for i in range(n_runs):
            progress.progress((i + 1) / n_runs, text=f"Trajectoire {i+1}/{n_runs}")
            
            # Sélection et exécution du simulateur
            if model == "Waterfall (Infini)":
                sim = TandemQueueSimulator(lambda_rate, mu1, mu2, K)
                jobs = sim.run(max_jobs=n_jobs, warmup_jobs=warmup)
                
                all_sojourn.extend([j.sojourn_time() for j in jobs])
                all_wait_s1.extend([j.waiting_time_s1() for j in jobs])
                all_wait_s2.extend([j.waiting_time_s2() for j in jobs])
            
            elif model == "Files Finies":
                sim = FiniteQueueSimulator(lambda_rate, mu1, mu2, K, ks, kf)
                results = sim.run(max_jobs=n_jobs, warmup_jobs=warmup)
                
                all_sojourn.extend(results.get('sojourn_times', []))
                all_rejected.append(results['rejection_rate'])
                all_lost.append(results['loss_rate'])
            
            elif model == "Backup":
                mode_map = {"Aucun": BackupMode.NONE, "Systématique": BackupMode.SYSTEMATIC, "Aléatoire": BackupMode.RANDOM}
                sim = BackupQueueSimulator(
                    lambda_rate, mu1, mu2, K, ks, kf,
                    backup_mode=mode_map[backup_mode],
                    backup_prob=backup_prob,
                    backup_time_mean=backup_time
                )
                results = sim.run(max_jobs=n_jobs, warmup_jobs=warmup)
                
                # BackupQueueSimulator retourne mean_sojourn, pas une liste de jobs
                if results.get('mean_sojourn', 0) > 0:
                    all_sojourn.append(results['mean_sojourn'])
                all_rejected.append(results.get('rejection_rate', 0))
                all_lost.append(results.get('blank_page_rate', 0))
            
            elif model == "Populations":
                # Calculer max_time basé sur n_jobs et lambda
                max_time = n_jobs / (lambda_ing + lambda_prepa) * 1.5
                warmup_time = warmup / (lambda_ing + lambda_prepa) * 1.5
                
                sim = MultiPopulationSimulator(
                    lambda_ing=lambda_ing, lambda_prepa=lambda_prepa,
                    mu1_ing=mu1_ing, mu1_prepa=mu1_prepa,
                    mu2_ing=mu2, mu2_prepa=mu2,
                    K=K
                )
                results = sim.run(max_time=max_time, warmup_time=warmup_time)
                
                # Résultats par population
                if 'ING' in results:
                    sojourn_ing.extend(results['ING'].get('sojourn_times', []))
                if 'PREPA' in results:
                    sojourn_prepa.extend(results['PREPA'].get('sojourn_times', []))
                all_sojourn.extend(sojourn_ing + sojourn_prepa)
            
            elif model == "Throttling":
                max_time = n_jobs / (lambda_ing + lambda_prepa) * 1.5
                warmup_time = warmup / (lambda_ing + lambda_prepa) * 1.5
                
                sim = BlockingQueueSimulator(
                    lambda_ing=lambda_ing, lambda_prepa=lambda_prepa,
                    mu1_ing=mu1_ing, mu1_prepa=mu1_prepa,
                    mu2_ing=mu2, mu2_prepa=mu2,
                    K=K,
                    tb=t_block
                )
                results = sim.run(max_time=max_time, warmup_time=warmup_time)
                
                if 'ING' in results:
                    sojourn_ing.extend(results['ING'].get('sojourn_times', []))
                if 'PREPA' in results:
                    sojourn_prepa.extend(results['PREPA'].get('sojourn_times', []))
                all_sojourn.extend(sojourn_ing + sojourn_prepa)
        
        progress.empty()
        
        # ==========================================================================
        # RÉSULTATS
        # ==========================================================================
        
        st.subheader("📈 Résultats")
        
        # Métriques principales
        stats = compute_stats(all_sojourn)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Temps séjour moyen", f"{stats['mean']:.3f}")
        with col2:
            st.metric("Écart-type", f"{stats['std']:.3f}")
        with col3:
            st.metric("Médiane", f"{stats['median']:.3f}")
        with col4:
            st.metric("Max", f"{stats['max']:.3f}")
    
            # Métriques de rejet/perte si applicable
            if all_rejected or all_lost:
                col1, col2 = st.columns(2)
                with col1:
                    if all_rejected:
                        st.metric("Taux de rejet moyen", f"{np.mean(all_rejected)*100:.2f}%")
                with col2:
                    if all_lost:
                        label = "Pages blanches" if model == "Backup" else "Taux de perte"
                        st.metric(label, f"{np.mean(all_lost)*100:.2f}%")
    
            # Métriques par population
            if model in ["Populations", "Throttling"] and sojourn_ing and sojourn_prepa:
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Séjour moyen ING", f"{np.mean(sojourn_ing):.3f}")
                with col2:
                    st.metric("Séjour moyen PREPA", f"{np.mean(sojourn_prepa):.3f}")
    
        st.markdown("---")
        
        # ==========================================================================
        # GRAPHIQUES
        # ==========================================================================
        
        tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "Comparaison", "Analyse", "💰 Coûts"])
        
        with tab1:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            
            # Histogramme temps de séjour
            axes[0].hist(all_sojourn, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='white')
            axes[0].axvline(stats['mean'], color='red', linestyle='--', label=f"μ = {stats['mean']:.2f}")
            axes[0].set_xlabel("Temps de séjour")
            axes[0].set_ylabel("Densité")
            axes[0].set_title("Distribution du temps de séjour")
            axes[0].legend()
    
        # Box plot
        if model in ["Populations", "Throttling"] and sojourn_ing and sojourn_prepa:
            data = [sojourn_ing, sojourn_prepa]
            labels = ["ING", "PREPA"]
            colors = ['#4CAF50', '#FF9800']
            bp = axes[1].boxplot(data, tick_labels=labels, patch_artist=True)
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            axes[1].set_ylabel("Temps de séjour")
            axes[1].set_title("Comparaison par population")
        else:
            # CDF
            sorted_data = np.sort(all_sojourn)
            cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            axes[1].plot(sorted_data, cdf, color='steelblue', linewidth=2)
            axes[1].axhline(0.95, color='red', linestyle='--', alpha=0.7, label='95e percentile')
            p95 = np.percentile(all_sojourn, 95)
            axes[1].axvline(p95, color='red', linestyle='--', alpha=0.7)
            axes[1].set_xlabel("Temps de séjour")
            axes[1].set_ylabel("CDF")
            axes[1].set_title("Fonction de répartition")
            axes[1].legend()
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        with tab2:
            if model in ["Populations", "Throttling"] and sojourn_ing and sojourn_prepa:
                fig, ax = plt.subplots(figsize=(10, 5))
        
                bins = np.linspace(0, max(max(sojourn_ing), max(sojourn_prepa)), 40)
                ax.hist(sojourn_ing, bins=bins, density=True, alpha=0.6, label='ING', color='#4CAF50')
                ax.hist(sojourn_prepa, bins=bins, density=True, alpha=0.6, label='PREPA', color='#FF9800')
                ax.axvline(np.mean(sojourn_ing), color='#2E7D32', linestyle='--', linewidth=2)
                ax.axvline(np.mean(sojourn_prepa), color='#E65100', linestyle='--', linewidth=2)
                ax.set_xlabel("Temps de séjour")
                ax.set_ylabel("Densité")
                ax.legend()
                ax.set_title("Distribution par population")
        
                st.pyplot(fig)
                plt.close()
            else:
                fig, ax = plt.subplots(figsize=(10, 5))
        
                # Histogrammes attente S1 vs S2
                if all_wait_s1 and all_wait_s2:
                    ax.hist(all_wait_s1, bins=40, density=True, alpha=0.6, label='Attente S1', color='#2196F3')
                    ax.hist(all_wait_s2, bins=40, density=True, alpha=0.6, label='Attente S2', color='#9C27B0')
                    ax.set_xlabel("Temps d'attente")
                    ax.set_ylabel("Densité")
                    ax.legend()
                    ax.set_title("Temps d'attente par station")
                else:
                    ax.text(0.5, 0.5, "Non disponible pour ce modèle", ha='center', va='center', transform=ax.transAxes)
        
                st.pyplot(fig)
                plt.close()
        
        with tab3:
            # Vérification Loi de Little: L = λW
            if all_sojourn:
                W_mean = np.mean(all_sojourn)
                L_theorique = lambda_rate * W_mean
        
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("W (temps séjour moyen)", f"{W_mean:.4f}")
                with col2:
                    st.metric("L = λW (nb moyen dans système)", f"{L_theorique:.4f}")
        
                # Formule théorique M/M/1 pour comparaison (station 2)
                if rho2 < 1:
                    W_theo_s2 = 1 / (mu2 - lambda_rate)
                    st.caption(f"Théorique M/M/1 (S2 seule): W = 1/(μ₂-λ) = {W_theo_s2:.4f}")
        
                # Graphique percentiles
                fig, ax = plt.subplots(figsize=(10, 4))
                percentiles = [50, 75, 90, 95, 99]
                values = [np.percentile(all_sojourn, p) for p in percentiles]
        
                bars = ax.bar([f"P{p}" for p in percentiles], values, color='steelblue', alpha=0.8, edgecolor='white')
                ax.axhline(stats['mean'], color='red', linestyle='--', label=f'Moyenne: {stats["mean"]:.2f}')
                ax.set_ylabel("Temps de séjour")
                ax.set_title("Percentiles du temps de séjour")
                ax.legend()
        
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                            f'{val:.2f}', ha='center', va='bottom', fontsize=9)
        
                st.pyplot(fig)
                plt.close()
        
        with tab4:
            # ==========================================================================
            # ANALYSE ÉCONOMIQUE
            # ==========================================================================
    
            # Calcul des coûts
            mean_sojourn = stats['mean'] if all_sojourn else 0
            reject_rate = np.mean(all_rejected) if all_rejected else 0
            loss_rate = np.mean(all_lost) if all_lost else 0
    
            # Coûts d'infrastructure
            if model == "Files Finies" or model == "Backup":
                infra_cost = cost_server * K + cost_capacity * (ks + kf)
            else:
                infra_cost = cost_server * K
    
            # Coûts opérationnels (par job)
            operational_cost_per_job = (
                cost_sojourn * mean_sojourn +
                cost_reject * reject_rate +
                cost_loss * loss_rate
            )
    
            # Coût total estimé (pour n_jobs)
            n_effective_jobs = n_jobs - warmup
            total_operational = operational_cost_per_job * n_effective_jobs
            total_cost = infra_cost + total_operational
    
            # Affichage métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Coût Infrastructure", f"{infra_cost:.2f} €")
            with col2:
                st.metric("Coût/Job", f"{operational_cost_per_job:.4f} €")
            with col3:
                st.metric("Coût Total Estimé", f"{total_cost:.2f} €")
    
            st.markdown("---")
    
            # Décomposition des coûts
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
            # Pie chart - Répartition infrastructure vs opérationnel
            if total_cost > 0:
                sizes = [infra_cost, total_operational]
                labels = ['Infrastructure', 'Opérationnel']
                colors = ['#2196F3', '#FF9800']
                explode = (0.05, 0)
                axes[0].pie(sizes, explode=explode, labels=labels, colors=colors,
                           autopct='%1.1f%%', startangle=90)
                axes[0].set_title("Répartition des coûts")
    
            # Bar chart - Décomposition coût opérationnel
            cost_components = {
                'Temps séjour': cost_sojourn * mean_sojourn,
                'Rejets': cost_reject * reject_rate,
                'Pertes': cost_loss * loss_rate
            }
    
            bars = axes[1].bar(cost_components.keys(), cost_components.values(), 
                              color=['#4CAF50', '#f44336', '#9C27B0'], alpha=0.8)
            axes[1].set_ylabel("Coût par job (€)")
            axes[1].set_title("Décomposition coût opérationnel")
    
            for bar, val in zip(bars, cost_components.values()):
                if val > 0:
                    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001, 
                                f'{val:.4f}', ha='center', va='bottom', fontsize=9)
    
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
    
            # Table récapitulative
            st.markdown("**Détail des coûts**")
            capacity_total = ks + kf if model in ["Files Finies", "Backup"] else 0
            cost_data = {
                "Composante": ["Serveurs (K)", "Capacité (ks+kf)", "Temps séjour", "Rejets", "Pertes/Pages blanches"],
                "Quantité": [str(K), str(capacity_total) if capacity_total > 0 else "-", 
                            f"{mean_sojourn:.3f}", f"{reject_rate*100:.2f}%", f"{loss_rate*100:.2f}%"],
                "Coût unitaire": [f"{cost_server:.2f} €", f"{cost_capacity:.2f} €", 
                                 f"{cost_sojourn:.2f} €/u.t.", f"{cost_reject:.2f} €", f"{cost_loss:.2f} €"],
                "Coût total": [f"{cost_server * K:.2f} €", 
                              f"{cost_capacity * capacity_total:.2f} €" if capacity_total > 0 else "-",
                              f"{cost_sojourn * mean_sojourn:.4f} €/job",
                              f"{cost_reject * reject_rate:.4f} €/job",
                              f"{cost_loss * loss_rate:.4f} €/job"]
            }
            st.table(cost_data)
    
    else:
        # État initial - instructions minimales
        st.info("Configurez les paramètres dans la barre latérale et cliquez sur **Lancer simulation**")
        
        # Schéma du système
        st.markdown("""
        ```
        Arrivées (λ) → [Station 1: K serveurs, μ₁] → [Station 2: 1 serveur, μ₂] → Sortie
        ```
        """)

with main_tab2:
    # ==========================================================================
    # ÉTUDE PARAMÉTRIQUE - VARIATION DE λ
    # ==========================================================================
    
    st.markdown("### Étude paramétrique : impact de la charge (λ)")
    st.caption("Lance plusieurs simulations avec différentes valeurs de λ pour voir l'évolution des métriques.")
    
    col1, col2 = st.columns(2)
    with col1:
        lambda_min = st.number_input("λ min", 0.5, 5.0, 1.0, 0.5, key="lambda_min_param")
    with col2:
        lambda_max = st.number_input("λ max", 2.0, 15.0, 8.0, 0.5, key="lambda_max_param")
    
    col3, col4 = st.columns(2)
    with col3:
        n_points = st.slider("Nombre de points", 3, 10, 5, key="n_points_param")
    with col4:
        n_traj_param = st.slider("Trajectoires par point", 1, 20, 5, key="n_traj_param")
    
    if st.button("🚀 Lancer l'étude paramétrique", type="primary", key="btn_param"):
        lambda_values = np.linspace(lambda_min, lambda_max, n_points)
        
        results_param = {
            'lambda': [],
            'sojourn_mean': [],
            'sojourn_std': [],
            'reject_rate': [],
            'loss_rate': [],
            'rho1': [],
            'rho2': []
        }
        
        progress_param = st.progress(0, text="Étude en cours...")
        
        for i, lam in enumerate(lambda_values):
            progress_param.progress((i + 1) / n_points, text=f"λ = {lam:.1f}")
            
            sojourns = []
            rejects = []
            losses = []
            
            for _ in range(n_traj_param):
                if model == "Waterfall (Infini)":
                    sim = TandemQueueSimulator(lam, mu1, mu2, K)
                    jobs = sim.run(max_jobs=1000, warmup_jobs=100)
                    sojourns.extend([j.sojourn_time() for j in jobs])
                
                elif model == "Files Finies":
                    sim = FiniteQueueSimulator(lam, mu1, mu2, K, ks, kf)
                    res = sim.run(max_jobs=1000, warmup_jobs=100)
                    sojourns.extend(res.get('sojourn_times', []))
                    rejects.append(res.get('rejection_rate', 0))
                    losses.append(res.get('loss_rate', 0))
                
                elif model == "Backup":
                    mode_map = {"Aucun": BackupMode.NONE, "Systématique": BackupMode.SYSTEMATIC, "Aléatoire": BackupMode.RANDOM}
                    sim = BackupQueueSimulator(lam, mu1, mu2, K, ks, kf,
                                               backup_mode=mode_map[backup_mode],
                                               backup_prob=backup_prob,
                                               backup_time_mean=backup_time)
                    res = sim.run(max_jobs=1000, warmup_jobs=100)
                    if res.get('mean_sojourn', 0) > 0:
                        sojourns.append(res['mean_sojourn'])
                    rejects.append(res.get('rejection_rate', 0))
                    losses.append(res.get('blank_page_rate', 0))
                
                elif model == "Populations":
                    # Répartir lambda proportionnellement
                    ratio = lambda_ing / (lambda_ing + lambda_prepa)
                    lam_i = lam * ratio
                    lam_p = lam * (1 - ratio)
                    max_time = 500
                    sim = MultiPopulationSimulator(
                        lambda_ing=lam_i, lambda_prepa=lam_p,
                        mu1_ing=mu1_ing, mu1_prepa=mu1_prepa,
                        mu2_ing=mu2, mu2_prepa=mu2, K=K
                    )
                    res = sim.run(max_time=max_time, warmup_time=50)
                    for pop in ['ING', 'PREPA']:
                        if pop in res:
                            sojourns.extend(res[pop].get('sojourn_times', []))
                
                elif model == "Throttling":
                    ratio = lambda_ing / (lambda_ing + lambda_prepa)
                    lam_i = lam * ratio
                    lam_p = lam * (1 - ratio)
                    max_time = 500
                    sim = BlockingQueueSimulator(
                        lambda_ing=lam_i, lambda_prepa=lam_p,
                        mu1_ing=mu1_ing, mu1_prepa=mu1_prepa,
                        mu2_ing=mu2, mu2_prepa=mu2, K=K, tb=t_block
                    )
                    res = sim.run(max_time=max_time, warmup_time=50)
                    for pop in ['ING', 'PREPA']:
                        if pop in res:
                            sojourns.extend(res[pop].get('sojourn_times', []))
            
            results_param['lambda'].append(lam)
            results_param['sojourn_mean'].append(np.mean(sojourns) if sojourns else 0)
            results_param['sojourn_std'].append(np.std(sojourns) if sojourns else 0)
            results_param['reject_rate'].append(np.mean(rejects) * 100 if rejects else 0)
            results_param['loss_rate'].append(np.mean(losses) * 100 if losses else 0)
            results_param['rho1'].append(lam / (K * mu1))
            results_param['rho2'].append(lam / mu2)
        
        progress_param.empty()
        
        # Graphiques
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 1. Temps de séjour moyen
        axes[0, 0].errorbar(results_param['lambda'], results_param['sojourn_mean'],
                           yerr=results_param['sojourn_std'], fmt='o-', capsize=3, 
                           color='steelblue', linewidth=2, markersize=6)
        axes[0, 0].set_xlabel("λ (taux d'arrivée)")
        axes[0, 0].set_ylabel("E[W] (temps de séjour)")
        axes[0, 0].set_title("Temps de séjour moyen")
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Taux de rejet et perte
        if any(results_param['reject_rate']) or any(results_param['loss_rate']):
            axes[0, 1].plot(results_param['lambda'], results_param['reject_rate'], 
                           'o-', color='#f44336', linewidth=2, label='Rejet (%)', markersize=6)
            axes[0, 1].plot(results_param['lambda'], results_param['loss_rate'], 
                           's-', color='#9C27B0', linewidth=2, label='Perte (%)', markersize=6)
            axes[0, 1].set_xlabel("λ (taux d'arrivée)")
            axes[0, 1].set_ylabel("Taux (%)")
            axes[0, 1].set_title("Taux de rejet et perte")
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        else:
            axes[0, 1].text(0.5, 0.5, "N/A (files infinies)", ha='center', va='center', 
                           transform=axes[0, 1].transAxes, fontsize=12)
            axes[0, 1].set_title("Taux de rejet et perte")
        
        # 3. Charge (ρ)
        axes[1, 0].plot(results_param['lambda'], results_param['rho1'], 
                       'o-', color='#2196F3', linewidth=2, label='ρ₁ (Station 1)', markersize=6)
        axes[1, 0].plot(results_param['lambda'], results_param['rho2'], 
                       's-', color='#FF9800', linewidth=2, label='ρ₂ (Station 2)', markersize=6)
        axes[1, 0].axhline(1.0, color='red', linestyle='--', linewidth=2, label='Limite stabilité')
        axes[1, 0].axhline(0.8, color='orange', linestyle=':', alpha=0.7)
        axes[1, 0].set_xlabel("λ (taux d'arrivée)")
        axes[1, 0].set_ylabel("ρ (charge)")
        axes[1, 0].set_title("Charge des stations")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, max(1.5, max(results_param['rho2']) * 1.1))
        
        # 4. Zone de stabilité
        lambdas = np.array(results_param['lambda'])
        stable = np.array(results_param['rho2']) < 1.0
        colors = ['#4CAF50' if s else '#f44336' for s in stable]
        axes[1, 1].bar(lambdas, results_param['sojourn_mean'], color=colors, alpha=0.7, width=0.3)
        axes[1, 1].set_xlabel("λ (taux d'arrivée)")
        axes[1, 1].set_ylabel("E[W]")
        axes[1, 1].set_title("Stabilité (🟢 stable, 🔴 instable)")
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # Point de saturation
        critical_lambda = mu2  # λ_max pour ρ₂ < 1
        st.info(f"⚠️ **Point de saturation théorique** : λ_max = μ₂ = **{critical_lambda:.1f}** (ρ₂ = 1)")

