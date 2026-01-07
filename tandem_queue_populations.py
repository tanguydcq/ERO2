#!/usr/bin/env python3
"""
Simulation à événements discrets avec DEUX POPULATIONS d'arrivées.

Architecture du système :
    ING    (Poisson λ_ing, service court)   ─┐
                                              ├→ [Station 1: M/M/K] → [Station 2: M/M/1] → Sortie
    PREPA  (Poisson λ_prepa, service long)  ─┘

Caractéristiques :
- ING   : étudiants ingénieurs, code optimisé, tests rapides
- PREPA : étudiants prépa, code moins optimisé, tests longs

Les deux flux arrivent indépendamment mais partagent les mêmes serveurs.
Analyse séparée des temps de séjour par population.

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import random
import heapq
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto


# =============================================================================
# TYPES ET STRUCTURES
# =============================================================================

class EventType(Enum):
    ARRIVAL_ING = auto()
    ARRIVAL_PREPA = auto()
    DEPARTURE_STATION1 = auto()
    DEPARTURE_STATION2 = auto()


class Population(Enum):
    ING = "ING"
    PREPA = "PREPA"


@dataclass
class Job:
    """Représente un job avec sa population d'origine."""
    job_id: int
    population: Population
    arrival_time: float
    
    # Timestamps
    start_service_s1: Optional[float] = None
    end_service_s1: Optional[float] = None
    start_service_s2: Optional[float] = None
    departure_time: Optional[float] = None
    
    # Temps de service (pour analyse)
    service_time_s1: float = 0.0
    service_time_s2: float = 0.0
    
    def sojourn_time(self) -> float:
        """Temps de séjour total."""
        if self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return float('inf')
    
    def waiting_time_s1(self) -> float:
        """Temps d'attente en station 1."""
        if self.start_service_s1 is not None:
            return self.start_service_s1 - self.arrival_time
        return float('inf')
    
    def waiting_time_s2(self) -> float:
        """Temps d'attente en station 2."""
        if self.start_service_s2 is not None and self.end_service_s1 is not None:
            return self.start_service_s2 - self.end_service_s1
        return float('inf')
    
    def sojourn_s1(self) -> float:
        """Temps de séjour en station 1."""
        if self.end_service_s1 is not None:
            return self.end_service_s1 - self.arrival_time
        return float('inf')
    
    def sojourn_s2(self) -> float:
        """Temps de séjour en station 2."""
        if self.departure_time is not None and self.end_service_s1 is not None:
            return self.departure_time - self.end_service_s1
        return float('inf')


@dataclass(order=True)
class Event:
    time: float
    event_type: EventType = field(compare=False)
    job: Job = field(compare=False)


# =============================================================================
# SIMULATEUR MULTI-POPULATION
# =============================================================================

class MultiPopulationSimulator:
    """
    Simulateur avec deux populations indépendantes.
    
    Paramètres de service différenciés :
    - ING   : μ1_ing (rapide), μ2_ing (rapide)
    - PREPA : μ1_prepa (lent), μ2_prepa (lent)
    """
    
    def __init__(
        self,
        # Taux d'arrivée par population
        lambda_ing: float,
        lambda_prepa: float,
        # Taux de service station 1 (par population)
        mu1_ing: float,
        mu1_prepa: float,
        # Taux de service station 2 (par population)
        mu2_ing: float,
        mu2_prepa: float,
        # Infrastructure
        K: int,
        ks: int = 100,   # Capacité station 1
        kf: int = 50,    # Capacité station 2
    ):
        """
        Args:
            lambda_ing: Taux d'arrivée ING
            lambda_prepa: Taux d'arrivée PREPA
            mu1_ing: Taux service S1 pour ING (élevé = service court)
            mu1_prepa: Taux service S1 pour PREPA (faible = service long)
            mu2_ing: Taux service S2 pour ING
            mu2_prepa: Taux service S2 pour PREPA
            K: Nombre de serveurs station 1
            ks, kf: Capacités
        """
        self.lambda_ing = lambda_ing
        self.lambda_prepa = lambda_prepa
        self.mu1_ing = mu1_ing
        self.mu1_prepa = mu1_prepa
        self.mu2_ing = mu2_ing
        self.mu2_prepa = mu2_prepa
        self.K = K
        self.ks = max(ks, K)
        self.kf = max(kf, 1)
        
        # Calculs théoriques
        self.lambda_total = lambda_ing + lambda_prepa
        self.prop_ing = lambda_ing / self.lambda_total if self.lambda_total > 0 else 0.5
        
        # Temps de service moyen pondéré
        self.mean_service_s1 = (
            self.prop_ing / mu1_ing + (1 - self.prop_ing) / mu1_prepa
        )
        self.mean_service_s2 = (
            self.prop_ing / mu2_ing + (1 - self.prop_ing) / mu2_prepa
        )
        
        self._reset()
    
    def _reset(self):
        """Réinitialise l'état."""
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        
        # Station 1
        self.queue_s1: List[Job] = []
        self.servers_s1: List[Optional[Job]] = [None] * self.K
        
        # Station 2
        self.queue_s2: List[Job] = []
        self.server_s2: Optional[Job] = None
        
        # Compteurs par population
        self.job_counter = 0
        self.completed_jobs: Dict[Population, List[Job]] = {
            Population.ING: [],
            Population.PREPA: []
        }
        self.rejected_jobs: Dict[Population, List[Job]] = {
            Population.ING: [],
            Population.PREPA: []
        }
        self.lost_jobs: Dict[Population, List[Job]] = {
            Population.ING: [],
            Population.PREPA: []
        }
        
        # Statistiques
        self.stats = {
            Population.ING: {'arrivals': 0, 'rejections': 0, 'losses': 0, 'completions': 0},
            Population.PREPA: {'arrivals': 0, 'rejections': 0, 'losses': 0, 'completions': 0}
        }
    
    def _schedule_event(self, event: Event):
        heapq.heappush(self.event_queue, event)
    
    def _generate_interarrival_ing(self) -> float:
        return random.expovariate(self.lambda_ing) if self.lambda_ing > 0 else float('inf')
    
    def _generate_interarrival_prepa(self) -> float:
        return random.expovariate(self.lambda_prepa) if self.lambda_prepa > 0 else float('inf')
    
    def _generate_service_s1(self, pop: Population) -> float:
        """Génère un temps de service selon la population."""
        if pop == Population.ING:
            return random.expovariate(self.mu1_ing)
        else:
            return random.expovariate(self.mu1_prepa)
    
    def _generate_service_s2(self, pop: Population) -> float:
        """Génère un temps de service selon la population."""
        if pop == Population.ING:
            return random.expovariate(self.mu2_ing)
        else:
            return random.expovariate(self.mu2_prepa)
    
    def _find_free_server_s1(self) -> int:
        for i, server in enumerate(self.servers_s1):
            if server is None:
                return i
        return -1
    
    def _count_jobs_station1(self) -> int:
        in_service = sum(1 for s in self.servers_s1 if s is not None)
        return in_service + len(self.queue_s1)
    
    def _count_jobs_station2(self) -> int:
        in_service = 1 if self.server_s2 is not None else 0
        return in_service + len(self.queue_s2)
    
    def _handle_arrival(self, job: Job, event_type: EventType):
        """Traite l'arrivée d'un job (ING ou PREPA)."""
        pop = job.population
        self.stats[pop]['arrivals'] += 1
        
        # Programmer la prochaine arrivée de cette population
        self.job_counter += 1
        if event_type == EventType.ARRIVAL_ING:
            next_arrival_time = self.current_time + self._generate_interarrival_ing()
            next_job = Job(
                job_id=self.job_counter,
                population=Population.ING,
                arrival_time=next_arrival_time
            )
            self._schedule_event(Event(
                time=next_arrival_time,
                event_type=EventType.ARRIVAL_ING,
                job=next_job
            ))
        else:
            next_arrival_time = self.current_time + self._generate_interarrival_prepa()
            next_job = Job(
                job_id=self.job_counter,
                population=Population.PREPA,
                arrival_time=next_arrival_time
            )
            self._schedule_event(Event(
                time=next_arrival_time,
                event_type=EventType.ARRIVAL_PREPA,
                job=next_job
            ))
        
        # Vérifier capacité station 1
        if self._count_jobs_station1() >= self.ks:
            self.rejected_jobs[pop].append(job)
            self.stats[pop]['rejections'] += 1
            return
        
        # Acceptation
        free_server = self._find_free_server_s1()
        if free_server >= 0:
            job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1(pop)
            job.service_time_s1 = service_time
            job.end_service_s1 = self.current_time + service_time
            self.servers_s1[free_server] = job
            
            self._schedule_event(Event(
                time=job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=job
            ))
        else:
            self.queue_s1.append(job)
    
    def _handle_departure_s1(self, job: Job):
        """Fin de service station 1."""
        pop = job.population
        
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # Prendre le prochain en file (FIFO, pas de priorité)
        if self.queue_s1:
            next_job = self.queue_s1.pop(0)
            next_job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1(next_job.population)
            next_job.service_time_s1 = service_time
            next_job.end_service_s1 = self.current_time + service_time
            
            free_server = self._find_free_server_s1()
            self.servers_s1[free_server] = next_job
            
            self._schedule_event(Event(
                time=next_job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=next_job
            ))
        
        # Vérifier capacité station 2
        if self._count_jobs_station2() >= self.kf:
            self.lost_jobs[pop].append(job)
            self.stats[pop]['losses'] += 1
            return
        
        # Entrée en station 2
        if self.server_s2 is None:
            job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2(pop)
            job.service_time_s2 = service_time
            job.departure_time = self.current_time + service_time
            self.server_s2 = job
            
            self._schedule_event(Event(
                time=job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=job
            ))
        else:
            self.queue_s2.append(job)
    
    def _handle_departure_s2(self, job: Job):
        """Fin de service station 2."""
        pop = job.population
        self.server_s2 = None
        self.completed_jobs[pop].append(job)
        self.stats[pop]['completions'] += 1
        
        if self.queue_s2:
            next_job = self.queue_s2.pop(0)
            next_pop = next_job.population
            next_job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2(next_pop)
            next_job.service_time_s2 = service_time
            next_job.departure_time = self.current_time + service_time
            self.server_s2 = next_job
            
            self._schedule_event(Event(
                time=next_job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=next_job
            ))
    
    def run(self, max_time: float = 10000.0, warmup_time: float = 1000.0) -> Dict:
        """
        Exécute la simulation.
        
        Args:
            max_time: Durée maximale de simulation
            warmup_time: Période de chauffe à ignorer
        """
        self._reset()
        
        # Programmer les premières arrivées
        if self.lambda_ing > 0:
            first_ing = Job(
                job_id=0,
                population=Population.ING,
                arrival_time=self._generate_interarrival_ing()
            )
            self._schedule_event(Event(
                time=first_ing.arrival_time,
                event_type=EventType.ARRIVAL_ING,
                job=first_ing
            ))
        
        if self.lambda_prepa > 0:
            self.job_counter += 1
            first_prepa = Job(
                job_id=self.job_counter,
                population=Population.PREPA,
                arrival_time=self._generate_interarrival_prepa()
            )
            self._schedule_event(Event(
                time=first_prepa.arrival_time,
                event_type=EventType.ARRIVAL_PREPA,
                job=first_prepa
            ))
        
        # Boucle principale
        while self.current_time < max_time and self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if self.current_time > max_time:
                break
            
            if event.event_type == EventType.ARRIVAL_ING:
                self._handle_arrival(event.job, EventType.ARRIVAL_ING)
            elif event.event_type == EventType.ARRIVAL_PREPA:
                self._handle_arrival(event.job, EventType.ARRIVAL_PREPA)
            elif event.event_type == EventType.DEPARTURE_STATION1:
                self._handle_departure_s1(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION2:
                self._handle_departure_s2(event.job)
        
        # Filtrer les jobs après warmup
        results = {}
        
        for pop in [Population.ING, Population.PREPA]:
            steady_jobs = [j for j in self.completed_jobs[pop] 
                          if j.arrival_time >= warmup_time]
            
            sojourn_times = [j.sojourn_time() for j in steady_jobs]
            waiting_s1 = [j.waiting_time_s1() for j in steady_jobs]
            waiting_s2 = [j.waiting_time_s2() for j in steady_jobs]
            sojourn_s1 = [j.sojourn_s1() for j in steady_jobs]
            sojourn_s2 = [j.sojourn_s2() for j in steady_jobs]
            service_s1 = [j.service_time_s1 for j in steady_jobs]
            service_s2 = [j.service_time_s2 for j in steady_jobs]
            
            results[pop.value] = {
                'completions': len(steady_jobs),
                'sojourn_times': sojourn_times,
                'mean_sojourn': mean(sojourn_times) if sojourn_times else 0,
                'std_sojourn': std(sojourn_times) if sojourn_times else 0,
                'mean_waiting_s1': mean(waiting_s1) if waiting_s1 else 0,
                'mean_waiting_s2': mean(waiting_s2) if waiting_s2 else 0,
                'mean_sojourn_s1': mean(sojourn_s1) if sojourn_s1 else 0,
                'mean_sojourn_s2': mean(sojourn_s2) if sojourn_s2 else 0,
                'mean_service_s1': mean(service_s1) if service_s1 else 0,
                'mean_service_s2': mean(service_s2) if service_s2 else 0,
                'percentile_50': percentile(sojourn_times, 0.5),
                'percentile_90': percentile(sojourn_times, 0.9),
                'percentile_99': percentile(sojourn_times, 0.99),
            }
        
        return results


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))


def percentile(values: List[float], p: float) -> float:
    """Calcule le percentile p (entre 0 et 1)."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(p * (len(sorted_vals) - 1))
    return sorted_vals[idx]


def compute_histogram(values: List[float], n_bins: int = 50) -> Tuple[List[float], List[float]]:
    """Calcule un histogramme."""
    if not values:
        return [], []
    
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return [min_val], [len(values)]
    
    bin_width = (max_val - min_val) / n_bins
    bins = [min_val + i * bin_width for i in range(n_bins + 1)]
    counts = [0] * n_bins
    
    for v in values:
        bin_idx = min(int((v - min_val) / bin_width), n_bins - 1)
        counts[bin_idx] += 1
    
    # Normaliser
    total = sum(counts)
    densities = [c / (total * bin_width) for c in counts]
    
    # Centres des bins
    centers = [min_val + (i + 0.5) * bin_width for i in range(n_bins)]
    
    return centers, densities


# =============================================================================
# FONCTIONS D'ANALYSE
# =============================================================================

def run_comparison_study(
    lambda_ing: float,
    lambda_prepa: float,
    mu1_ing: float,
    mu1_prepa: float,
    mu2_ing: float,
    mu2_prepa: float,
    K: int,
    n_trajectories: int = 20,
    max_time: float = 10000.0,
    warmup_time: float = 1000.0
) -> Dict:
    """
    Exécute plusieurs trajectoires et agrège les résultats.
    """
    results_ing = {
        'sojourn_all': [],
        'mean_sojourns': [],
        'mean_waiting_s1': [],
        'mean_waiting_s2': [],
    }
    results_prepa = {
        'sojourn_all': [],
        'mean_sojourns': [],
        'mean_waiting_s1': [],
        'mean_waiting_s2': [],
    }
    
    print(f"\n{'='*70}")
    print("SIMULATION MULTI-POPULATION")
    print(f"{'='*70}")
    print(f"ING   : λ={lambda_ing}, μ1={mu1_ing}, μ2={mu2_ing} (service court)")
    print(f"PREPA : λ={lambda_prepa}, μ1={mu1_prepa}, μ2={mu2_prepa} (service long)")
    print(f"Serveurs K={K}")
    print(f"{'='*70}\n")
    
    for i in range(n_trajectories):
        sim = MultiPopulationSimulator(
            lambda_ing=lambda_ing,
            lambda_prepa=lambda_prepa,
            mu1_ing=mu1_ing,
            mu1_prepa=mu1_prepa,
            mu2_ing=mu2_ing,
            mu2_prepa=mu2_prepa,
            K=K
        )
        
        res = sim.run(max_time=max_time, warmup_time=warmup_time)
        
        # ING
        if res['ING']['sojourn_times']:
            results_ing['sojourn_all'].extend(res['ING']['sojourn_times'])
            results_ing['mean_sojourns'].append(res['ING']['mean_sojourn'])
            results_ing['mean_waiting_s1'].append(res['ING']['mean_waiting_s1'])
            results_ing['mean_waiting_s2'].append(res['ING']['mean_waiting_s2'])
        
        # PREPA
        if res['PREPA']['sojourn_times']:
            results_prepa['sojourn_all'].extend(res['PREPA']['sojourn_times'])
            results_prepa['mean_sojourns'].append(res['PREPA']['mean_sojourn'])
            results_prepa['mean_waiting_s1'].append(res['PREPA']['mean_waiting_s1'])
            results_prepa['mean_waiting_s2'].append(res['PREPA']['mean_waiting_s2'])
        
        if (i + 1) % 5 == 0:
            print(f"Trajectoire {i+1}/{n_trajectories}")
    
    return {
        'ING': {
            'sojourn_all': results_ing['sojourn_all'],
            'mean_sojourn': mean(results_ing['mean_sojourns']),
            'std_sojourn': std(results_ing['mean_sojourns']),
            'mean_waiting_s1': mean(results_ing['mean_waiting_s1']),
            'mean_waiting_s2': mean(results_ing['mean_waiting_s2']),
            'percentile_50': percentile(results_ing['sojourn_all'], 0.5),
            'percentile_90': percentile(results_ing['sojourn_all'], 0.9),
            'percentile_99': percentile(results_ing['sojourn_all'], 0.99),
        },
        'PREPA': {
            'sojourn_all': results_prepa['sojourn_all'],
            'mean_sojourn': mean(results_prepa['mean_sojourns']),
            'std_sojourn': std(results_prepa['mean_sojourns']),
            'mean_waiting_s1': mean(results_prepa['mean_waiting_s1']),
            'mean_waiting_s2': mean(results_prepa['mean_waiting_s2']),
            'percentile_50': percentile(results_prepa['sojourn_all'], 0.5),
            'percentile_90': percentile(results_prepa['sojourn_all'], 0.9),
            'percentile_99': percentile(results_prepa['sojourn_all'], 0.99),
        }
    }


def vary_ratio_study(
    lambda_total: float,
    ratios: List[float],  # proportion d'ING
    mu1_ing: float,
    mu1_prepa: float,
    mu2_ing: float,
    mu2_prepa: float,
    K: int,
    n_trajectories: int = 15,
    max_time: float = 8000.0,
    warmup_time: float = 1000.0
) -> Dict:
    """
    Étudie l'impact du ratio ING/PREPA sur les temps de séjour.
    """
    results = {
        'ratio': ratios,
        'ing_mean': [],
        'ing_std': [],
        'prepa_mean': [],
        'prepa_std': [],
        'global_mean': [],
    }
    
    print(f"\n{'='*70}")
    print("ÉTUDE DE L'IMPACT DU RATIO ING/PREPA")
    print(f"{'='*70}")
    print(f"λ total = {lambda_total}")
    print(f"{'='*70}\n")
    
    for ratio in ratios:
        lambda_ing = lambda_total * ratio
        lambda_prepa = lambda_total * (1 - ratio)
        
        ing_means = []
        prepa_means = []
        
        for _ in range(n_trajectories):
            sim = MultiPopulationSimulator(
                lambda_ing=lambda_ing,
                lambda_prepa=lambda_prepa,
                mu1_ing=mu1_ing,
                mu1_prepa=mu1_prepa,
                mu2_ing=mu2_ing,
                mu2_prepa=mu2_prepa,
                K=K
            )
            
            res = sim.run(max_time=max_time, warmup_time=warmup_time)
            
            if res['ING']['sojourn_times']:
                ing_means.append(res['ING']['mean_sojourn'])
            if res['PREPA']['sojourn_times']:
                prepa_means.append(res['PREPA']['mean_sojourn'])
        
        results['ing_mean'].append(mean(ing_means) if ing_means else 0)
        results['ing_std'].append(std(ing_means) if ing_means else 0)
        results['prepa_mean'].append(mean(prepa_means) if prepa_means else 0)
        results['prepa_std'].append(std(prepa_means) if prepa_means else 0)
        
        # Moyenne globale pondérée
        if ing_means and prepa_means:
            global_m = ratio * mean(ing_means) + (1 - ratio) * mean(prepa_means)
        else:
            global_m = mean(ing_means) if ing_means else mean(prepa_means)
        results['global_mean'].append(global_m)
        
        print(f"Ratio ING={ratio*100:5.1f}%: E[W]_ING={results['ing_mean'][-1]:.3f}, "
              f"E[W]_PREPA={results['prepa_mean'][-1]:.3f}")
    
    return results


# =============================================================================
# GRAPHIQUES
# =============================================================================

def plot_population_comparison(results: Dict, save_path: str = "population_comparison.png"):
    """Génère les graphiques de comparaison des populations."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparaison des Populations ING vs PREPA\n'
                 '(Temps de service différenciés)', 
                 fontsize=14, fontweight='bold')
    
    colors = {'ING': '#3498db', 'PREPA': '#e74c3c'}
    
    # 1. Distributions des temps de séjour
    ax1 = axes[0, 0]
    for pop in ['ING', 'PREPA']:
        if results[pop]['sojourn_all']:
            centers, densities = compute_histogram(results[pop]['sojourn_all'], n_bins=50)
            ax1.plot(centers, densities, color=colors[pop], 
                     label=f'{pop} (μ={results[pop]["mean_sojourn"]:.2f})',
                     linewidth=2)
            ax1.fill_between(centers, densities, alpha=0.3, color=colors[pop])
    ax1.set_xlabel('Temps de séjour', fontsize=11)
    ax1.set_ylabel('Densité', fontsize=11)
    ax1.set_title('Distribution des Temps de Séjour', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Comparaison des moyennes
    ax2 = axes[0, 1]
    pops = ['ING', 'PREPA']
    x = range(len(pops))
    
    means = [results[p]['mean_sojourn'] for p in pops]
    stds = [results[p]['std_sojourn'] for p in pops]
    
    bars = ax2.bar(x, means, yerr=stds, capsize=8, 
                   color=[colors[p] for p in pops], alpha=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(pops)
    ax2.set_ylabel('Temps de séjour moyen E[W]', fontsize=11)
    ax2.set_title('Temps de Séjour Moyen par Population', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for bar, m in zip(bars, means):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{m:.3f}', ha='center', va='bottom', fontsize=11)
    
    # 3. Décomposition du temps de séjour
    ax3 = axes[1, 0]
    width = 0.35
    x = range(len(pops))
    
    waiting_s1 = [results[p]['mean_waiting_s1'] for p in pops]
    waiting_s2 = [results[p]['mean_waiting_s2'] for p in pops]
    
    # Calculer le temps de service moyen
    service_s1 = [1/4.0, 1/1.0]  # Approximation basée sur les paramètres
    service_s2 = [1/8.0, 1/3.0]
    
    ax3.bar(x, waiting_s1, width, label='Attente S1', color='#3498db', alpha=0.7)
    ax3.bar(x, waiting_s2, width, bottom=waiting_s1, 
            label='Attente S2', color='#e74c3c', alpha=0.7)
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(pops)
    ax3.set_ylabel('Temps d\'attente', fontsize=11)
    ax3.set_title('Décomposition du Temps d\'Attente', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Percentiles
    ax4 = axes[1, 1]
    percentiles_labels = ['P50', 'P90', 'P99']
    x = range(len(percentiles_labels))
    width = 0.35
    
    ing_perc = [results['ING']['percentile_50'], 
                results['ING']['percentile_90'],
                results['ING']['percentile_99']]
    prepa_perc = [results['PREPA']['percentile_50'],
                  results['PREPA']['percentile_90'],
                  results['PREPA']['percentile_99']]
    
    ax4.bar([i - width/2 for i in x], ing_perc, width, label='ING', color=colors['ING'])
    ax4.bar([i + width/2 for i in x], prepa_perc, width, label='PREPA', color=colors['PREPA'])
    
    ax4.set_xticks(x)
    ax4.set_xticklabels(percentiles_labels)
    ax4.set_ylabel('Temps de séjour', fontsize=11)
    ax4.set_title('Percentiles du Temps de Séjour', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def plot_ratio_study(results: Dict, save_path: str = "ratio_study.png"):
    """Graphique de l'étude du ratio."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ratios = [r * 100 for r in results['ratio']]  # En pourcentage
    
    ax.errorbar(ratios, results['ing_mean'], yerr=results['ing_std'],
                fmt='o-', capsize=4, color='#3498db', linewidth=2,
                markersize=8, label='ING')
    ax.errorbar(ratios, results['prepa_mean'], yerr=results['prepa_std'],
                fmt='s-', capsize=4, color='#e74c3c', linewidth=2,
                markersize=8, label='PREPA')
    ax.plot(ratios, results['global_mean'], '^--', color='#27ae60',
            linewidth=2, markersize=8, label='Moyenne globale')
    
    ax.set_xlabel('Proportion d\'ING (%)', fontsize=12)
    ax.set_ylabel('Temps de séjour moyen E[W]', fontsize=12)
    ax.set_title('Impact du Ratio ING/PREPA sur les Temps de Séjour', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def plot_detailed_distributions(results: Dict, save_path: str = "distributions_detail.png"):
    """Graphiques détaillés des distributions."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Distributions Détaillées des Temps de Séjour', 
                 fontsize=14, fontweight='bold')
    
    colors = {'ING': '#3498db', 'PREPA': '#e74c3c'}
    
    for idx, pop in enumerate(['ING', 'PREPA']):
        ax = axes[idx]
        sojourns = results[pop]['sojourn_all']
        
        if sojourns:
            # Histogramme
            centers, densities = compute_histogram(sojourns, n_bins=40)
            ax.bar(centers, densities, width=centers[1]-centers[0] if len(centers) > 1 else 1,
                   color=colors[pop], alpha=0.7, edgecolor='black', linewidth=0.5)
            
            # Ligne de moyenne
            m = results[pop]['mean_sojourn']
            ax.axvline(m, color='black', linestyle='--', linewidth=2,
                       label=f'Moyenne = {m:.3f}')
            
            # Percentiles
            p50 = results[pop]['percentile_50']
            p90 = results[pop]['percentile_90']
            ax.axvline(p50, color='green', linestyle=':', linewidth=2,
                       label=f'P50 = {p50:.3f}')
            ax.axvline(p90, color='orange', linestyle=':', linewidth=2,
                       label=f'P90 = {p90:.3f}')
        
        ax.set_xlabel('Temps de séjour', fontsize=11)
        ax.set_ylabel('Densité', fontsize=11)
        ax.set_title(f'Population {pop}', fontsize=12)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def print_comparison_table(results: Dict):
    """Affiche un tableau comparatif."""
    print(f"\n{'='*80}")
    print("ANALYSE COMPARATIVE DES POPULATIONS")
    print(f"{'='*80}")
    
    print(f"\n{'Métrique':<30} | {'ING':>15} | {'PREPA':>15} | {'Ratio P/I':>12}")
    print(f"{'-'*30}-+-{'-'*15}-+-{'-'*15}-+-{'-'*12}")
    
    metrics = [
        ('Temps de séjour moyen', 'mean_sojourn'),
        ('Écart-type', 'std_sojourn'),
        ('Attente moyenne S1', 'mean_waiting_s1'),
        ('Attente moyenne S2', 'mean_waiting_s2'),
        ('Percentile 50%', 'percentile_50'),
        ('Percentile 90%', 'percentile_90'),
        ('Percentile 99%', 'percentile_99'),
    ]
    
    for name, key in metrics:
        ing_val = results['ING'].get(key, 0)
        prepa_val = results['PREPA'].get(key, 0)
        ratio = prepa_val / ing_val if ing_val > 0 else float('inf')
        print(f"{name:<30} | {ing_val:>15.4f} | {prepa_val:>15.4f} | {ratio:>12.2f}x")
    
    print(f"\n{'='*80}")
    
    # Résumé
    ing_m = results['ING']['mean_sojourn']
    prepa_m = results['PREPA']['mean_sojourn']
    overhead = (prepa_m - ing_m) / ing_m * 100 if ing_m > 0 else 0
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   • Les PREPA ont un temps de séjour {overhead:.1f}% plus long que les ING")
    print(f"   • Différence absolue : {prepa_m - ing_m:.3f} unités de temps")
    print(f"   • Ratio P90/P50 ING   : {results['ING']['percentile_90']/results['ING']['percentile_50']:.2f}x")
    print(f"   • Ratio P90/P50 PREPA : {results['PREPA']['percentile_90']/results['PREPA']['percentile_50']:.2f}x")
    print(f"{'='*80}\n")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    print("\n" + "👥 " * 20)
    print("   SIMULATEUR MULTI-POPULATION (ING vs PREPA)")
    print("👥 " * 20)
    
    # =========================================================================
    # PARAMÈTRES
    # =========================================================================
    
    # Taux d'arrivée
    LAMBDA_ING = 3.0      # ING arrivent plus souvent
    LAMBDA_PREPA = 2.0    # PREPA arrivent moins souvent
    
    # Taux de service Station 1 (exécution des tests)
    MU1_ING = 4.0         # ING : code optimisé, tests rapides (E[S]=0.25)
    MU1_PREPA = 1.0       # PREPA : code moins optimisé, tests longs (E[S]=1.0)
    
    # Taux de service Station 2 (envoi des résultats)
    MU2_ING = 8.0         # ING : petits fichiers (E[S]=0.125)
    MU2_PREPA = 3.0       # PREPA : gros fichiers de log (E[S]=0.33)
    
    # Infrastructure
    K = 4
    
    # Simulation
    N_TRAJECTORIES = 20
    MAX_TIME = 10000.0
    WARMUP_TIME = 1000.0
    
    random.seed(42)
    
    # =========================================================================
    # 1. COMPARAISON DES POPULATIONS
    # =========================================================================
    
    results = run_comparison_study(
        lambda_ing=LAMBDA_ING,
        lambda_prepa=LAMBDA_PREPA,
        mu1_ing=MU1_ING,
        mu1_prepa=MU1_PREPA,
        mu2_ing=MU2_ING,
        mu2_prepa=MU2_PREPA,
        K=K,
        n_trajectories=N_TRAJECTORIES,
        max_time=MAX_TIME,
        warmup_time=WARMUP_TIME
    )
    
    # Afficher le tableau
    print_comparison_table(results)
    
    # Graphiques
    print("\n📊 Génération des graphiques...")
    plot_population_comparison(results, save_path="img/population_comparison.png")
    plot_detailed_distributions(results, save_path="img/distributions_detail.png")
    
    # =========================================================================
    # 2. ÉTUDE DE L'IMPACT DU RATIO ING/PREPA
    # =========================================================================
    
    print("\n" + "="*70)
    print("ÉTUDE DE L'IMPACT DU RATIO")
    print("="*70)
    
    LAMBDA_TOTAL = 5.0
    RATIOS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    ratio_results = vary_ratio_study(
        lambda_total=LAMBDA_TOTAL,
        ratios=RATIOS,
        mu1_ing=MU1_ING,
        mu1_prepa=MU1_PREPA,
        mu2_ing=MU2_ING,
        mu2_prepa=MU2_PREPA,
        K=K,
        n_trajectories=15,
        max_time=8000.0,
        warmup_time=1000.0
    )
    
    plot_ratio_study(ratio_results, save_path="img/ratio_study.png")
    
    # =========================================================================
    # 3. CONCLUSIONS
    # =========================================================================
    
    print("\n" + "="*80)
    print("📋 CONCLUSIONS DE L'ANALYSE")
    print("="*80)
    
    print(f"""
    1. DIFFÉRENCES OBSERVÉES:
       • ING   : E[W] = {results['ING']['mean_sojourn']:.3f} (service rapide)
       • PREPA : E[W] = {results['PREPA']['mean_sojourn']:.3f} (service lent)
       • Surcoût PREPA : +{(results['PREPA']['mean_sojourn']/results['ING']['mean_sojourn']-1)*100:.0f}%
    
    2. DISTRIBUTION:
       • ING   : distribution plus concentrée (faible variance)
       • PREPA : queue de distribution plus longue (cas extrêmes)
    
    3. IMPACT DU RATIO:
       • Plus d'ING → meilleure performance globale
       • Les PREPA "pénalisent" les ING via l'attente partagée
       • Effet asymétrique : PREPA impactés par ING (préemption de serveurs)
    
    4. RECOMMANDATIONS:
       • Séparer les files si possible (équité)
       • Limiter le ratio PREPA pour garantir QoS
       • Adapter le nombre de serveurs K selon la charge PREPA
    """)
    
    return results, ratio_results


if __name__ == "__main__":
    results, ratio_results = main()
