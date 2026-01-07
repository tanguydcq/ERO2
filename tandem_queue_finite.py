#!/usr/bin/env python3
"""
Simulation à événements discrets d'un réseau de files d'attente en tandem
avec CAPACITÉS FINIES.

Architecture du système :
    Arrivées (Poisson λ) → [Station 1: M/M/K/ks] → [Station 2: M/M/1/kf] → Sortie

Station 1 : K serveurs parallèles, capacité totale ks (file + serveurs)
Station 2 : 1 serveur, capacité totale kf (file + serveur)

Nouveautés par rapport à la version infinie :
- Rejet à l'entrée si station 1 pleine (push tags rejetés)
- Perte entre stations si station 2 pleine (résultats perdus)
- Métriques de rejet et perte
- Graphiques d'analyse paramétrique

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import random
import heapq
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto


# =============================================================================
# CONSTANTES ET TYPES D'ÉVÉNEMENTS
# =============================================================================

class EventType(Enum):
    """Types d'événements possibles dans la simulation."""
    ARRIVAL = auto()
    DEPARTURE_STATION1 = auto()
    DEPARTURE_STATION2 = auto()


class JobStatus(Enum):
    """Statut final d'un job."""
    COMPLETED = auto()      # Job terminé avec succès
    REJECTED = auto()       # Rejeté à l'entrée (station 1 pleine)
    LOST = auto()           # Perdu entre stations (station 2 pleine)


@dataclass
class Job:
    """
    Représente un job dans le système.
    """
    job_id: int
    arrival_time: float
    status: JobStatus = JobStatus.COMPLETED
    start_service_s1: Optional[float] = None
    end_service_s1: Optional[float] = None
    start_service_s2: Optional[float] = None
    departure_time: Optional[float] = None
    
    def sojourn_time(self) -> float:
        """Temps de séjour total (seulement pour jobs complétés)."""
        if self.status == JobStatus.COMPLETED and self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return float('inf')


@dataclass(order=True)
class Event:
    """Représente un événement dans la simulation."""
    time: float
    event_type: EventType = field(compare=False)
    job: Job = field(compare=False)


# =============================================================================
# SIMULATEUR AVEC CAPACITÉS FINIES
# =============================================================================

class FiniteQueueSimulator:
    """
    Simulateur à événements discrets pour M/M/K/ks -> M/M/1/kf.
    
    Attributes:
        lambda_rate: Taux d'arrivée
        mu1: Taux de service station 1 (par serveur)
        mu2: Taux de service station 2
        K: Nombre de serveurs station 1
        ks: Capacité totale station 1 (file + K serveurs)
        kf: Capacité totale station 2 (file + 1 serveur)
    """
    
    def __init__(self, lambda_rate: float, mu1: float, mu2: float, 
                 K: int, ks: int, kf: int):
        """
        Initialise le simulateur.
        
        Args:
            lambda_rate: Taux d'arrivée λ
            mu1: Taux de service μ1
            mu2: Taux de service μ2
            K: Nombre de serveurs station 1
            ks: Capacité station 1 (doit être >= K)
            kf: Capacité station 2 (doit être >= 1)
        """
        self.lambda_rate = lambda_rate
        self.mu1 = mu1
        self.mu2 = mu2
        self.K = K
        self.ks = max(ks, K)  # Au minimum K places (les serveurs)
        self.kf = max(kf, 1)  # Au minimum 1 place (le serveur)
        
        # Capacité de la file d'attente (hors serveurs)
        self.queue_capacity_s1 = self.ks - K
        self.queue_capacity_s2 = self.kf - 1
        
        self._reset()
    
    def _reset(self):
        """Réinitialise l'état du simulateur."""
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        
        # État station 1
        self.queue_s1: List[Job] = []
        self.servers_s1: List[Optional[Job]] = [None] * self.K
        
        # État station 2
        self.queue_s2: List[Job] = []
        self.server_s2: Optional[Job] = None
        
        # Compteurs
        self.job_counter = 0
        self.completed_jobs: List[Job] = []
        self.rejected_jobs: List[Job] = []  # Rejetés à l'entrée
        self.lost_jobs: List[Job] = []       # Perdus entre stations
        
        # Statistiques de débit
        self.total_arrivals = 0
        self.total_rejections = 0
        self.total_losses = 0
        self.total_completions = 0
    
    def _schedule_event(self, event: Event):
        """Ajoute un événement à l'échéancier."""
        heapq.heappush(self.event_queue, event)
    
    def _generate_interarrival(self) -> float:
        return random.expovariate(self.lambda_rate)
    
    def _generate_service_s1(self) -> float:
        return random.expovariate(self.mu1)
    
    def _generate_service_s2(self) -> float:
        return random.expovariate(self.mu2)
    
    def _find_free_server_s1(self) -> int:
        for i, server in enumerate(self.servers_s1):
            if server is None:
                return i
        return -1
    
    def _count_jobs_station1(self) -> int:
        """Compte le nombre total de jobs dans la station 1."""
        in_service = sum(1 for s in self.servers_s1 if s is not None)
        in_queue = len(self.queue_s1)
        return in_service + in_queue
    
    def _count_jobs_station2(self) -> int:
        """Compte le nombre total de jobs dans la station 2."""
        in_service = 1 if self.server_s2 is not None else 0
        in_queue = len(self.queue_s2)
        return in_service + in_queue
    
    def _handle_arrival(self, job: Job):
        """Traite l'arrivée d'un nouveau job."""
        self.total_arrivals += 1
        
        # Programmer la prochaine arrivée
        self.job_counter += 1
        next_job = Job(
            job_id=self.job_counter, 
            arrival_time=self.current_time + self._generate_interarrival()
        )
        self._schedule_event(Event(
            time=next_job.arrival_time,
            event_type=EventType.ARRIVAL,
            job=next_job
        ))
        
        # Vérifier si la station 1 est pleine
        current_load = self._count_jobs_station1()
        
        if current_load >= self.ks:
            # REJET : station 1 pleine
            job.status = JobStatus.REJECTED
            self.rejected_jobs.append(job)
            self.total_rejections += 1
            return
        
        # Acceptation du job
        free_server = self._find_free_server_s1()
        
        if free_server >= 0:
            # Service immédiat
            job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1()
            job.end_service_s1 = self.current_time + service_time
            self.servers_s1[free_server] = job
            
            self._schedule_event(Event(
                time=job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=job
            ))
        else:
            # Mise en file d'attente (on a déjà vérifié qu'il y a de la place)
            self.queue_s1.append(job)
    
    def _handle_departure_s1(self, job: Job):
        """Traite la fin de service à la station 1."""
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # Prendre le prochain job en attente à la station 1
        if self.queue_s1:
            next_job = self.queue_s1.pop(0)
            next_job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1()
            next_job.end_service_s1 = self.current_time + service_time
            
            free_server = self._find_free_server_s1()
            self.servers_s1[free_server] = next_job
            
            self._schedule_event(Event(
                time=next_job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=next_job
            ))
        
        # Vérifier si la station 2 peut accepter le job
        current_load_s2 = self._count_jobs_station2()
        
        if current_load_s2 >= self.kf:
            # PERTE : station 2 pleine
            job.status = JobStatus.LOST
            self.lost_jobs.append(job)
            self.total_losses += 1
            return
        
        # Transfer vers station 2
        if self.server_s2 is None:
            # Service immédiat
            job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2()
            job.departure_time = self.current_time + service_time
            self.server_s2 = job
            
            self._schedule_event(Event(
                time=job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=job
            ))
        else:
            # Mise en file d'attente station 2
            self.queue_s2.append(job)
    
    def _handle_departure_s2(self, job: Job):
        """Traite la fin de service à la station 2."""
        self.server_s2 = None
        job.status = JobStatus.COMPLETED
        self.completed_jobs.append(job)
        self.total_completions += 1
        
        if self.queue_s2:
            next_job = self.queue_s2.pop(0)
            next_job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2()
            next_job.departure_time = self.current_time + service_time
            self.server_s2 = next_job
            
            self._schedule_event(Event(
                time=next_job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=next_job
            ))
    
    def run(self, max_jobs: int = 10000, warmup_jobs: int = 1000) -> Dict:
        """
        Exécute la simulation.
        
        Returns:
            Dictionnaire avec les métriques
        """
        self._reset()
        
        # Première arrivée
        first_job = Job(job_id=0, arrival_time=self._generate_interarrival())
        self._schedule_event(Event(
            time=first_job.arrival_time,
            event_type=EventType.ARRIVAL,
            job=first_job
        ))
        
        # Compteurs pour la période post-warmup
        warmup_arrivals = 0
        warmup_rejections = 0
        warmup_losses = 0
        warmup_completions = 0
        warmup_done = False
        
        while self.job_counter < max_jobs and self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            # Détecter la fin du warmup
            if not warmup_done and self.job_counter >= warmup_jobs:
                warmup_done = True
                warmup_arrivals = self.total_arrivals
                warmup_rejections = self.total_rejections
                warmup_losses = self.total_losses
                warmup_completions = self.total_completions
            
            if event.event_type == EventType.ARRIVAL:
                self._handle_arrival(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION1:
                self._handle_departure_s1(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION2:
                self._handle_departure_s2(event.job)
        
        # Métriques post-warmup
        steady_arrivals = self.total_arrivals - warmup_arrivals
        steady_rejections = self.total_rejections - warmup_rejections
        steady_losses = self.total_losses - warmup_losses
        steady_completions = self.total_completions - warmup_completions
        
        # Jobs complétés après warmup
        steady_completed = [j for j in self.completed_jobs if j.job_id >= warmup_jobs]
        sojourn_times = [j.sojourn_time() for j in steady_completed]
        
        # Calcul des taux
        rejection_rate = steady_rejections / steady_arrivals if steady_arrivals > 0 else 0
        
        # Taux de perte = jobs perdus / jobs ayant passé station 1
        jobs_passed_s1 = steady_arrivals - steady_rejections
        loss_rate = steady_losses / jobs_passed_s1 if jobs_passed_s1 > 0 else 0
        
        # Throughput effectif
        throughput = steady_completions / (self.current_time - 0) if self.current_time > 0 else 0
        
        return {
            'arrivals': steady_arrivals,
            'rejections': steady_rejections,
            'losses': steady_losses,
            'completions': steady_completions,
            'rejection_rate': rejection_rate,
            'loss_rate': loss_rate,
            'throughput': throughput,
            'sojourn_times': sojourn_times,
            'mean_sojourn': sum(sojourn_times) / len(sojourn_times) if sojourn_times else 0,
            'var_sojourn': self._variance(sojourn_times) if sojourn_times else 0,
        }
    
    @staticmethod
    def _variance(values: List[float]) -> float:
        """Calcule la variance empirique."""
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        return sum((x - mean) ** 2 for x in values) / (n - 1)


# =============================================================================
# FONCTIONS D'ANALYSE ET GRAPHIQUES
# =============================================================================

def run_parameter_study(
    lambda_values: List[float],
    mu1: float,
    mu2: float,
    K: int,
    ks: int,
    kf: int,
    n_trajectories: int = 10,
    jobs_per_traj: int = 10000,
    warmup: int = 1000,
    seed: int = None
) -> Dict:
    """
    Étude paramétrique : fait varier λ et collecte les métriques.
    
    Returns:
        Dictionnaire avec les résultats pour chaque valeur de λ
    """
    if seed is not None:
        random.seed(seed)
    
    results = {
        'lambda': lambda_values,
        'rejection_rate_mean': [],
        'rejection_rate_std': [],
        'loss_rate_mean': [],
        'loss_rate_std': [],
        'sojourn_mean': [],
        'sojourn_std': [],
        'throughput_mean': [],
        'throughput_std': [],
    }
    
    print(f"\n{'='*70}")
    print(f"ÉTUDE PARAMÉTRIQUE : Variation de λ")
    print(f"{'='*70}")
    print(f"Paramètres fixes: μ1={mu1}, μ2={mu2}, K={K}, ks={ks}, kf={kf}")
    print(f"Trajectoires: {n_trajectories}, Jobs/traj: {jobs_per_traj}")
    print(f"{'='*70}\n")
    
    for lam in lambda_values:
        rejection_rates = []
        loss_rates = []
        sojourns = []
        throughputs = []
        
        for _ in range(n_trajectories):
            sim = FiniteQueueSimulator(lam, mu1, mu2, K, ks, kf)
            res = sim.run(max_jobs=jobs_per_traj, warmup_jobs=warmup)
            
            rejection_rates.append(res['rejection_rate'])
            loss_rates.append(res['loss_rate'])
            if res['mean_sojourn'] > 0:
                sojourns.append(res['mean_sojourn'])
            throughputs.append(res['throughput'])
        
        # Moyennes et écarts-types
        results['rejection_rate_mean'].append(mean(rejection_rates))
        results['rejection_rate_std'].append(std(rejection_rates))
        results['loss_rate_mean'].append(mean(loss_rates))
        results['loss_rate_std'].append(std(loss_rates))
        results['sojourn_mean'].append(mean(sojourns) if sojourns else 0)
        results['sojourn_std'].append(std(sojourns) if sojourns else 0)
        results['throughput_mean'].append(mean(throughputs))
        results['throughput_std'].append(std(throughputs))
        
        print(f"λ = {lam:5.2f} | Rejet: {results['rejection_rate_mean'][-1]*100:5.2f}% | "
              f"Perte: {results['loss_rate_mean'][-1]*100:5.2f}% | "
              f"E[W]: {results['sojourn_mean'][-1]:6.3f} | "
              f"Débit: {results['throughput_mean'][-1]:5.3f}")
    
    return results


def mean(values: List[float]) -> float:
    """Moyenne d'une liste."""
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    """Écart-type d'une liste."""
    n = len(values)
    if n < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))


def plot_results(results: Dict, save_path: str = "queue_analysis.png"):
    """
    Génère les graphiques d'analyse.
    
    Args:
        results: Résultats de l'étude paramétrique
        save_path: Chemin pour sauvegarder la figure
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  matplotlib non disponible. Installation en cours...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'matplotlib'])
        import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Analyse du Réseau de Files d\'Attente avec Capacités Finies\n'
                 '(M/M/K/ks → M/M/1/kf)', fontsize=14, fontweight='bold')
    
    lambda_vals = results['lambda']
    
    # =========================================================================
    # Graphique 1 : Taux de rejet (push tags rejetés)
    # =========================================================================
    ax1 = axes[0, 0]
    rejection_pct = [r * 100 for r in results['rejection_rate_mean']]
    rejection_err = [r * 100 for r in results['rejection_rate_std']]
    
    ax1.errorbar(lambda_vals, rejection_pct, yerr=rejection_err, 
                 fmt='o-', capsize=4, color='#e74c3c', linewidth=2, 
                 markersize=8, label='Taux de rejet')
    ax1.fill_between(lambda_vals, 
                     [r - e for r, e in zip(rejection_pct, rejection_err)],
                     [r + e for r, e in zip(rejection_pct, rejection_err)],
                     alpha=0.2, color='#e74c3c')
    ax1.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax1.set_ylabel('Taux de rejet (%)', fontsize=11)
    ax1.set_title('📛 Taux de Rejet des Push Tags\n(Station 1 pleine)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    ax1.legend()
    
    # =========================================================================
    # Graphique 2 : Taux de perte des résultats
    # =========================================================================
    ax2 = axes[0, 1]
    loss_pct = [r * 100 for r in results['loss_rate_mean']]
    loss_err = [r * 100 for r in results['loss_rate_std']]
    
    ax2.errorbar(lambda_vals, loss_pct, yerr=loss_err,
                 fmt='s-', capsize=4, color='#e67e22', linewidth=2,
                 markersize=8, label='Taux de perte')
    ax2.fill_between(lambda_vals,
                     [r - e for r, e in zip(loss_pct, loss_err)],
                     [r + e for r, e in zip(loss_pct, loss_err)],
                     alpha=0.2, color='#e67e22')
    ax2.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax2.set_ylabel('Taux de perte (%)', fontsize=11)
    ax2.set_title('⚠️ Taux de Perte des Résultats\n(Station 2 pleine)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)
    ax2.legend()
    
    # =========================================================================
    # Graphique 3 : Temps de séjour moyen
    # =========================================================================
    ax3 = axes[1, 0]
    sojourn = results['sojourn_mean']
    sojourn_err = results['sojourn_std']
    
    ax3.errorbar(lambda_vals, sojourn, yerr=sojourn_err,
                 fmt='^-', capsize=4, color='#3498db', linewidth=2,
                 markersize=8, label='Temps de séjour')
    ax3.fill_between(lambda_vals,
                     [s - e for s, e in zip(sojourn, sojourn_err)],
                     [s + e for s, e in zip(sojourn, sojourn_err)],
                     alpha=0.2, color='#3498db')
    ax3.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax3.set_ylabel('Temps de séjour E[W]', fontsize=11)
    ax3.set_title('⏱️ Temps de Séjour Total\n(Jobs complétés uniquement)', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # =========================================================================
    # Graphique 4 : Débit effectif
    # =========================================================================
    ax4 = axes[1, 1]
    throughput = results['throughput_mean']
    throughput_err = results['throughput_std']
    
    ax4.errorbar(lambda_vals, throughput, yerr=throughput_err,
                 fmt='D-', capsize=4, color='#27ae60', linewidth=2,
                 markersize=8, label='Débit effectif')
    ax4.plot(lambda_vals, lambda_vals, '--', color='gray', 
             alpha=0.5, label='λ (débit idéal)')
    ax4.fill_between(lambda_vals,
                     [t - e for t, e in zip(throughput, throughput_err)],
                     [t + e for t, e in zip(throughput, throughput_err)],
                     alpha=0.2, color='#27ae60')
    ax4.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax4.set_ylabel('Débit (jobs/temps)', fontsize=11)
    ax4.set_title('📈 Débit Effectif du Système\n(Throughput)', fontsize=12)
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def plot_capacity_comparison(mu1: float, mu2: float, K: int, 
                             lambda_vals: List[float],
                             capacity_configs: List[Tuple[int, int]],
                             n_traj: int = 10,
                             save_path: str = "capacity_comparison.png"):
    """
    Compare plusieurs configurations de capacité.
    
    Args:
        capacity_configs: Liste de tuples (ks, kf)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'matplotlib'])
        import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Comparaison des Configurations de Capacité', 
                 fontsize=14, fontweight='bold')
    
    colors = ['#e74c3c', '#3498db', '#27ae60', '#9b59b6', '#f39c12']
    
    for idx, (ks, kf) in enumerate(capacity_configs):
        results = run_parameter_study(
            lambda_vals, mu1, mu2, K, ks, kf,
            n_trajectories=n_traj, jobs_per_traj=5000, warmup=500
        )
        
        color = colors[idx % len(colors)]
        label = f'ks={ks}, kf={kf}'
        
        # Taux de rejet
        axes[0].plot(lambda_vals, 
                     [r * 100 for r in results['rejection_rate_mean']],
                     'o-', color=color, label=label, linewidth=2)
        
        # Taux de perte
        axes[1].plot(lambda_vals,
                     [r * 100 for r in results['loss_rate_mean']],
                     's-', color=color, label=label, linewidth=2)
        
        # Temps de séjour
        axes[2].plot(lambda_vals, results['sojourn_mean'],
                     '^-', color=color, label=label, linewidth=2)
    
    axes[0].set_xlabel('λ')
    axes[0].set_ylabel('Taux de rejet (%)')
    axes[0].set_title('Rejets (Station 1)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_xlabel('λ')
    axes[1].set_ylabel('Taux de perte (%)')
    axes[1].set_title('Pertes (Station 2)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    axes[2].set_xlabel('λ')
    axes[2].set_ylabel('E[W]')
    axes[2].set_title('Temps de séjour')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def print_detailed_results(results: Dict):
    """Affiche un tableau récapitulatif."""
    print(f"\n{'='*80}")
    print("TABLEAU RÉCAPITULATIF")
    print(f"{'='*80}")
    print(f"{'λ':>6} | {'Rejet (%)':>10} | {'Perte (%)':>10} | "
          f"{'E[W]':>10} | {'Débit':>10}")
    print(f"{'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    
    for i, lam in enumerate(results['lambda']):
        print(f"{lam:6.2f} | {results['rejection_rate_mean'][i]*100:10.2f} | "
              f"{results['loss_rate_mean'][i]*100:10.2f} | "
              f"{results['sojourn_mean'][i]:10.4f} | "
              f"{results['throughput_mean'][i]:10.4f}")
    
    print(f"{'='*80}\n")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    print("\n" + "🚀 " * 20)
    print("   SIMULATEUR AVEC CAPACITÉS FINIES (M/M/K/ks → M/M/1/kf)")
    print("🚀 " * 20)
    
    # =========================================================================
    # PARAMÈTRES
    # =========================================================================
    
    # Paramètres du système
    MU1 = 2.0         # Taux de service station 1
    MU2 = 5.0         # Taux de service station 2
    K = 3             # Nombre de serveurs station 1
    KS = 10           # Capacité totale station 1 (file + serveurs)
    KF = 5            # Capacité totale station 2 (file + serveur)
    
    # Valeurs de λ à tester
    LAMBDA_VALUES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    # Paramètres de simulation
    N_TRAJECTORIES = 15
    JOBS_PER_TRAJ = 10000
    WARMUP = 1000
    SEED = 42
    
    # =========================================================================
    # EXÉCUTION DE L'ÉTUDE PARAMÉTRIQUE
    # =========================================================================
    
    random.seed(SEED)
    
    results = run_parameter_study(
        lambda_values=LAMBDA_VALUES,
        mu1=MU1,
        mu2=MU2,
        K=K,
        ks=KS,
        kf=KF,
        n_trajectories=N_TRAJECTORIES,
        jobs_per_traj=JOBS_PER_TRAJ,
        warmup=WARMUP,
        seed=SEED
    )
    
    # Affichage du tableau
    print_detailed_results(results)
    
    # =========================================================================
    # GÉNÉRATION DES GRAPHIQUES
    # =========================================================================
    
    print("\n📊 Génération des graphiques...")
    plot_results(results, save_path="img/queue_analysis.png")
    
    # =========================================================================
    # COMPARAISON DE CONFIGURATIONS
    # =========================================================================
    
    print("\n📊 Comparaison de différentes configurations de capacité...")
    
    capacity_configs = [
        (5, 3),    # Petites capacités
        (10, 5),   # Moyennes capacités
        (20, 10),  # Grandes capacités
        (50, 20),  # Très grandes capacités
    ]
    
    plot_capacity_comparison(
        mu1=MU1, mu2=MU2, K=K,
        lambda_vals=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        capacity_configs=capacity_configs,
        n_traj=10,
        save_path="img/capacity_comparison.png"
    )
    
    # =========================================================================
    # EXEMPLE D'UTILISATION SIMPLE
    # =========================================================================
    
    print("\n" + "="*60)
    print("💡 EXEMPLE D'UTILISATION SIMPLE")
    print("="*60)
    
    sim = FiniteQueueSimulator(
        lambda_rate=6.0,
        mu1=2.0,
        mu2=5.0,
        K=3,
        ks=10,
        kf=5
    )
    
    res = sim.run(max_jobs=10000, warmup_jobs=1000)
    
    print(f"\nRésultats pour λ=6.0:")
    print(f"  Arrivées totales     : {res['arrivals']}")
    print(f"  Jobs rejetés         : {res['rejections']} ({res['rejection_rate']*100:.2f}%)")
    print(f"  Jobs perdus          : {res['losses']} ({res['loss_rate']*100:.2f}%)")
    print(f"  Jobs complétés       : {res['completions']}")
    print(f"  Temps de séjour moyen: {res['mean_sojourn']:.4f}")
    print(f"  Variance temps séjour: {res['var_sojourn']:.4f}")
    print(f"  Débit effectif       : {res['throughput']:.4f}")
    
    return results


if __name__ == "__main__":
    results = main()
