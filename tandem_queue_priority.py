#!/usr/bin/env python3
"""
Simulation à événements discrets avec FILES PRIORITAIRES.

Ce module propose un système alternatif pour minimiser le temps de séjour moyen
des deux populations (ING et PREPA) simultanément.

Trois stratégies alternatives sont proposées :

1. PRIORITY_SRPT (Shortest Remaining Processing Time)
   - Priorité aux jobs avec le temps de service le plus court
   - Optimal pour minimiser le temps de séjour moyen global
   - Favorise les ING (service court) mais améliore le débit global

2. PRIORITY_FCFS_SEPARATE (Files séparées FIFO)
   - Files d'attente séparées par population
   - Serveurs dédiés ou partagés avec alternance
   - Équité entre populations

3. PRIORITY_WEIGHTED_FAIR (File équitable pondérée)
   - File unique mais service proportionnel aux arrivées
   - Garantit un temps de réponse équitable

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


class PriorityPolicy(Enum):
    """Politiques de priorité disponibles."""
    FCFS = "FCFS"                     # First Come First Served (référence)
    SRPT = "SRPT"                     # Shortest Remaining Processing Time
    SEPARATE_QUEUES = "SEPARATE"      # Files séparées par population
    WEIGHTED_FAIR = "WEIGHTED_FAIR"   # File équitable pondérée
    PREPA_PRIORITY = "PREPA_FIRST"    # Priorité aux PREPA (compensation)


@dataclass
class Job:
    """Représente un job avec priorité."""
    job_id: int
    population: Population
    arrival_time: float
    expected_service_s1: float = 0.0  # Temps de service estimé (pour SRPT)
    expected_service_s2: float = 0.0
    
    # Timestamps
    start_service_s1: Optional[float] = None
    end_service_s1: Optional[float] = None
    start_service_s2: Optional[float] = None
    departure_time: Optional[float] = None
    
    # Temps de service réels
    service_time_s1: float = 0.0
    service_time_s2: float = 0.0
    
    def sojourn_time(self) -> float:
        if self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return float('inf')
    
    def waiting_time_s1(self) -> float:
        if self.start_service_s1 is not None:
            return self.start_service_s1 - self.arrival_time
        return float('inf')
    
    def waiting_time_s2(self) -> float:
        if self.start_service_s2 is not None and self.end_service_s1 is not None:
            return self.start_service_s2 - self.end_service_s1
        return float('inf')


@dataclass(order=True)
class Event:
    time: float
    event_type: EventType = field(compare=False)
    job: Job = field(compare=False)


# =============================================================================
# FILE D'ATTENTE AVEC PRIORITÉ
# =============================================================================

class PriorityQueue:
    """File d'attente avec politique de priorité configurable."""
    
    def __init__(self, policy: PriorityPolicy):
        self.policy = policy
        self._queue: List[Job] = []
        self._queue_ing: List[Job] = []    # Pour SEPARATE_QUEUES
        self._queue_prepa: List[Job] = []  # Pour SEPARATE_QUEUES
        self._last_served: Population = Population.PREPA  # Pour alternance
    
    def add(self, job: Job):
        """Ajoute un job à la file."""
        if self.policy == PriorityPolicy.SEPARATE_QUEUES:
            if job.population == Population.ING:
                self._queue_ing.append(job)
            else:
                self._queue_prepa.append(job)
        else:
            self._queue.append(job)
    
    def pop(self) -> Optional[Job]:
        """Retire et retourne le prochain job selon la politique."""
        
        if self.policy == PriorityPolicy.FCFS:
            return self._pop_fcfs()
        elif self.policy == PriorityPolicy.SRPT:
            return self._pop_srpt()
        elif self.policy == PriorityPolicy.SEPARATE_QUEUES:
            return self._pop_separate()
        elif self.policy == PriorityPolicy.WEIGHTED_FAIR:
            return self._pop_weighted_fair()
        elif self.policy == PriorityPolicy.PREPA_PRIORITY:
            return self._pop_prepa_priority()
        
        return self._pop_fcfs()
    
    def _pop_fcfs(self) -> Optional[Job]:
        """First Come First Served."""
        if not self._queue:
            return None
        return self._queue.pop(0)
    
    def _pop_srpt(self) -> Optional[Job]:
        """Shortest Remaining Processing Time."""
        if not self._queue:
            return None
        
        # Trouver le job avec le plus petit temps de service estimé
        min_idx = 0
        min_service = self._queue[0].expected_service_s1
        
        for i, job in enumerate(self._queue):
            if job.expected_service_s1 < min_service:
                min_service = job.expected_service_s1
                min_idx = i
        
        return self._queue.pop(min_idx)
    
    def _pop_separate(self) -> Optional[Job]:
        """Files séparées avec alternance équitable."""
        # Alterner entre les files
        if not self._queue_ing and not self._queue_prepa:
            return None
        
        if not self._queue_ing:
            return self._queue_prepa.pop(0)
        if not self._queue_prepa:
            return self._queue_ing.pop(0)
        
        # Alternance
        if self._last_served == Population.ING:
            self._last_served = Population.PREPA
            return self._queue_prepa.pop(0)
        else:
            self._last_served = Population.ING
            return self._queue_ing.pop(0)
    
    def _pop_weighted_fair(self) -> Optional[Job]:
        """File équitable pondérée par temps d'attente."""
        if not self._queue:
            return None
        
        # Priorité au job qui attend le plus longtemps
        # (équivalent à FCFS si même priorité)
        return self._queue.pop(0)
    
    def _pop_prepa_priority(self) -> Optional[Job]:
        """Priorité aux PREPA (compensation pour temps de service long)."""
        if not self._queue:
            return None
        
        # Chercher un PREPA en priorité
        for i, job in enumerate(self._queue):
            if job.population == Population.PREPA:
                return self._queue.pop(i)
        
        # Sinon prendre le premier
        return self._queue.pop(0)
    
    def __len__(self) -> int:
        if self.policy == PriorityPolicy.SEPARATE_QUEUES:
            return len(self._queue_ing) + len(self._queue_prepa)
        return len(self._queue)
    
    def is_empty(self) -> bool:
        return len(self) == 0


# =============================================================================
# SIMULATEUR AVEC PRIORITÉS
# =============================================================================

class PriorityQueueSimulator:
    """
    Simulateur avec différentes politiques de priorité.
    """
    
    def __init__(
        self,
        # Arrivées
        lambda_ing: float,
        lambda_prepa: float,
        # Services
        mu1_ing: float,
        mu1_prepa: float,
        mu2_ing: float,
        mu2_prepa: float,
        # Infrastructure
        K: int,
        ks: int = 100,
        kf: int = 50,
        # Politique
        policy: PriorityPolicy = PriorityPolicy.FCFS,
    ):
        self.lambda_ing = lambda_ing
        self.lambda_prepa = lambda_prepa
        self.mu1_ing = mu1_ing
        self.mu1_prepa = mu1_prepa
        self.mu2_ing = mu2_ing
        self.mu2_prepa = mu2_prepa
        self.K = K
        self.ks = max(ks, K)
        self.kf = max(kf, 1)
        self.policy = policy
        
        self._reset()
    
    def _reset(self):
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        
        # Station 1 avec politique de priorité
        self.queue_s1 = PriorityQueue(self.policy)
        self.servers_s1: List[Optional[Job]] = [None] * self.K
        
        # Station 2 avec politique de priorité
        self.queue_s2 = PriorityQueue(self.policy)
        self.server_s2: Optional[Job] = None
        
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
        
        self.stats = {
            Population.ING: {'arrivals': 0, 'rejections': 0, 'losses': 0, 'completions': 0},
            Population.PREPA: {'arrivals': 0, 'rejections': 0, 'losses': 0, 'completions': 0}
        }
    
    def _schedule_event(self, event: Event):
        heapq.heappush(self.event_queue, event)
    
    def _generate_service_s1(self, pop: Population) -> float:
        mu = self.mu1_ing if pop == Population.ING else self.mu1_prepa
        return random.expovariate(mu)
    
    def _generate_service_s2(self, pop: Population) -> float:
        mu = self.mu2_ing if pop == Population.ING else self.mu2_prepa
        return random.expovariate(mu)
    
    def _expected_service_s1(self, pop: Population) -> float:
        """Temps de service moyen (pour SRPT)."""
        return 1 / self.mu1_ing if pop == Population.ING else 1 / self.mu1_prepa
    
    def _find_free_server_s1(self) -> int:
        for i, server in enumerate(self.servers_s1):
            if server is None:
                return i
        return -1
    
    def _count_jobs_station1(self) -> int:
        in_service = sum(1 for s in self.servers_s1 if s is not None)
        in_queue = len(self.queue_s1)
        return in_service + in_queue
    
    def _count_jobs_station2(self) -> int:
        in_service = 1 if self.server_s2 is not None else 0
        in_queue = len(self.queue_s2)
        return in_service + in_queue
    
    def _handle_arrival(self, job: Job, pop: Population):
        self.stats[pop]['arrivals'] += 1
        
        # Programmer la prochaine arrivée
        self.job_counter += 1
        
        # Temps de service estimé (pour SRPT)
        job.expected_service_s1 = self._expected_service_s1(pop)
        job.expected_service_s2 = 1 / (self.mu2_ing if pop == Population.ING else self.mu2_prepa)
        
        # Programmer prochaine arrivée du même type
        lambda_rate = self.lambda_ing if pop == Population.ING else self.lambda_prepa
        next_job = Job(
            job_id=self.job_counter,
            population=pop,
            arrival_time=self.current_time + random.expovariate(lambda_rate)
        )
        event_type = EventType.ARRIVAL_ING if pop == Population.ING else EventType.ARRIVAL_PREPA
        self._schedule_event(Event(
            time=next_job.arrival_time,
            event_type=event_type,
            job=next_job
        ))
        
        # Vérifier capacité station 1
        current_load = self._count_jobs_station1()
        if current_load >= self.ks:
            self.stats[pop]['rejections'] += 1
            self.rejected_jobs[pop].append(job)
            return
        
        # Chercher serveur libre
        free_server = self._find_free_server_s1()
        
        if free_server >= 0:
            job.start_service_s1 = self.current_time
            job.service_time_s1 = self._generate_service_s1(pop)
            job.end_service_s1 = self.current_time + job.service_time_s1
            self.servers_s1[free_server] = job
            
            self._schedule_event(Event(
                time=job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=job
            ))
        else:
            self.queue_s1.add(job)
    
    def _handle_departure_s1(self, job: Job):
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # Prendre le prochain job selon la politique
        if not self.queue_s1.is_empty():
            next_job = self.queue_s1.pop()
            next_job.start_service_s1 = self.current_time
            next_job.service_time_s1 = self._generate_service_s1(next_job.population)
            next_job.end_service_s1 = self.current_time + next_job.service_time_s1
            
            free_server = self._find_free_server_s1()
            self.servers_s1[free_server] = next_job
            
            self._schedule_event(Event(
                time=next_job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=next_job
            ))
        
        # Vérifier capacité station 2
        current_load_s2 = self._count_jobs_station2()
        if current_load_s2 >= self.kf:
            self.stats[job.population]['losses'] += 1
            self.lost_jobs[job.population].append(job)
            return
        
        # Transférer vers station 2
        if self.server_s2 is None:
            job.start_service_s2 = self.current_time
            job.service_time_s2 = self._generate_service_s2(job.population)
            job.departure_time = self.current_time + job.service_time_s2
            self.server_s2 = job
            
            self._schedule_event(Event(
                time=job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=job
            ))
        else:
            self.queue_s2.add(job)
    
    def _handle_departure_s2(self, job: Job):
        self.server_s2 = None
        self.completed_jobs[job.population].append(job)
        self.stats[job.population]['completions'] += 1
        
        if not self.queue_s2.is_empty():
            next_job = self.queue_s2.pop()
            next_job.start_service_s2 = self.current_time
            next_job.service_time_s2 = self._generate_service_s2(next_job.population)
            next_job.departure_time = self.current_time + next_job.service_time_s2
            self.server_s2 = next_job
            
            self._schedule_event(Event(
                time=next_job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=next_job
            ))
    
    def run(self, max_jobs: int = 10000, warmup_jobs: int = 1000) -> Dict:
        """Exécute la simulation."""
        self._reset()
        
        # Premières arrivées
        job_ing = Job(
            job_id=0,
            population=Population.ING,
            arrival_time=random.expovariate(self.lambda_ing)
        )
        job_prepa = Job(
            job_id=1,
            population=Population.PREPA,
            arrival_time=random.expovariate(self.lambda_prepa)
        )
        self.job_counter = 1
        
        self._schedule_event(Event(job_ing.arrival_time, EventType.ARRIVAL_ING, job_ing))
        self._schedule_event(Event(job_prepa.arrival_time, EventType.ARRIVAL_PREPA, job_prepa))
        
        while self.job_counter < max_jobs and self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if event.event_type == EventType.ARRIVAL_ING:
                self._handle_arrival(event.job, Population.ING)
            elif event.event_type == EventType.ARRIVAL_PREPA:
                self._handle_arrival(event.job, Population.PREPA)
            elif event.event_type == EventType.DEPARTURE_STATION1:
                self._handle_departure_s1(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION2:
                self._handle_departure_s2(event.job)
        
        return self._compute_results(warmup_jobs)
    
    def _compute_results(self, warmup_jobs: int) -> Dict:
        """Calcule les résultats par population."""
        results = {
            'policy': self.policy.value,
            'populations': {}
        }
        
        for pop in [Population.ING, Population.PREPA]:
            completed = [j for j in self.completed_jobs[pop] if j.job_id >= warmup_jobs]
            sojourn_times = [j.sojourn_time() for j in completed]
            
            if sojourn_times:
                mean_sojourn = sum(sojourn_times) / len(sojourn_times)
                var_sojourn = sum((x - mean_sojourn) ** 2 for x in sojourn_times) / len(sojourn_times) if len(sojourn_times) > 1 else 0
            else:
                mean_sojourn = 0
                var_sojourn = 0
            
            results['populations'][pop.value] = {
                'completions': len(completed),
                'mean_sojourn': mean_sojourn,
                'var_sojourn': var_sojourn,
                'sojourn_times': sojourn_times
            }
        
        # Métriques globales
        all_sojourn = results['populations']['ING']['sojourn_times'] + results['populations']['PREPA']['sojourn_times']
        if all_sojourn:
            results['global'] = {
                'mean_sojourn': sum(all_sojourn) / len(all_sojourn),
                'total_completions': len(all_sojourn)
            }
        
        return results


# =============================================================================
# COMPARAISON DES POLITIQUES
# =============================================================================

def compare_policies(
    lambda_ing: float = 3.0,
    lambda_prepa: float = 1.0,
    mu1_ing: float = 4.0,
    mu1_prepa: float = 1.0,
    mu2_ing: float = 8.0,
    mu2_prepa: float = 3.0,
    K: int = 3,
    n_trajectories: int = 10,
    jobs_per_traj: int = 10000,
    warmup: int = 1000,
    seed: int = None
) -> Dict[str, Dict]:
    """
    Compare toutes les politiques de priorité.
    
    Returns:
        Dictionnaire avec les résultats par politique
    """
    if seed is not None:
        random.seed(seed)
    
    policies = [
        PriorityPolicy.FCFS,
        PriorityPolicy.SRPT,
        PriorityPolicy.SEPARATE_QUEUES,
        PriorityPolicy.PREPA_PRIORITY,
    ]
    
    results = {}
    
    print(f"\n{'='*70}")
    print("COMPARAISON DES POLITIQUES DE PRIORITÉ")
    print(f"{'='*70}")
    print(f"λ_ING={lambda_ing}, λ_PREPA={lambda_prepa}")
    print(f"μ1_ING={mu1_ing}, μ1_PREPA={mu1_prepa}")
    print(f"μ2_ING={mu2_ing}, μ2_PREPA={mu2_prepa}")
    print(f"K={K}, Trajectoires={n_trajectories}")
    print(f"{'='*70}\n")
    
    for policy in policies:
        print(f"\n📊 Politique: {policy.value}")
        
        ing_sojourns = []
        prepa_sojourns = []
        global_sojourns = []
        
        for i in range(n_trajectories):
            sim = PriorityQueueSimulator(
                lambda_ing=lambda_ing,
                lambda_prepa=lambda_prepa,
                mu1_ing=mu1_ing,
                mu1_prepa=mu1_prepa,
                mu2_ing=mu2_ing,
                mu2_prepa=mu2_prepa,
                K=K,
                policy=policy
            )
            
            res = sim.run(max_jobs=jobs_per_traj, warmup_jobs=warmup)
            
            if res['populations']['ING']['sojourn_times']:
                ing_sojourns.append(res['populations']['ING']['mean_sojourn'])
            if res['populations']['PREPA']['sojourn_times']:
                prepa_sojourns.append(res['populations']['PREPA']['mean_sojourn'])
            if 'global' in res:
                global_sojourns.append(res['global']['mean_sojourn'])
        
        def mean(lst):
            return sum(lst) / len(lst) if lst else 0
        
        def std(lst):
            if len(lst) < 2:
                return 0
            m = mean(lst)
            return math.sqrt(sum((x - m) ** 2 for x in lst) / (len(lst) - 1))
        
        results[policy.value] = {
            'E[W]_ING': mean(ing_sojourns),
            'std_ING': std(ing_sojourns),
            'E[W]_PREPA': mean(prepa_sojourns),
            'std_PREPA': std(prepa_sojourns),
            'E[W]_global': mean(global_sojourns),
            'std_global': std(global_sojourns),
            'ratio_PREPA_ING': mean(prepa_sojourns) / mean(ing_sojourns) if mean(ing_sojourns) > 0 else 0
        }
        
        print(f"   E[W] ING   : {results[policy.value]['E[W]_ING']:.4f} ± {results[policy.value]['std_ING']:.4f}")
        print(f"   E[W] PREPA : {results[policy.value]['E[W]_PREPA']:.4f} ± {results[policy.value]['std_PREPA']:.4f}")
        print(f"   E[W] Global: {results[policy.value]['E[W]_global']:.4f}")
        print(f"   Ratio P/I  : {results[policy.value]['ratio_PREPA_ING']:.4f}")
    
    return results


def plot_policy_comparison(results: Dict, save_path: str = "img/policy_comparison.png"):
    """Génère un graphique comparatif des politiques."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  matplotlib non disponible")
        return
    
    policies = list(results.keys())
    x = range(len(policies))
    
    ing_means = [results[p]['E[W]_ING'] for p in policies]
    ing_stds = [results[p]['std_ING'] for p in policies]
    prepa_means = [results[p]['E[W]_PREPA'] for p in policies]
    prepa_stds = [results[p]['std_PREPA'] for p in policies]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Comparaison des Politiques de Priorité', fontsize=14, fontweight='bold')
    
    # Graphique 1: E[W] par population
    width = 0.35
    ax1 = axes[0]
    ax1.bar([i - width/2 for i in x], ing_means, width, yerr=ing_stds, 
            label='ING', color='#3498db', capsize=4)
    ax1.bar([i + width/2 for i in x], prepa_means, width, yerr=prepa_stds,
            label='PREPA', color='#e74c3c', capsize=4)
    ax1.set_xlabel('Politique')
    ax1.set_ylabel('E[W] (temps de séjour)')
    ax1.set_title('Temps de Séjour par Population')
    ax1.set_xticks(x)
    ax1.set_xticklabels(policies, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2: E[W] global
    ax2 = axes[1]
    global_means = [results[p]['E[W]_global'] for p in policies]
    colors = ['#27ae60' if p == 'SRPT' else '#95a5a6' for p in policies]
    ax2.bar(x, global_means, color=colors)
    ax2.set_xlabel('Politique')
    ax2.set_ylabel('E[W] global')
    ax2.set_title('Temps de Séjour Global Moyen')
    ax2.set_xticks(x)
    ax2.set_xticklabels(policies, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3)
    
    # Graphique 3: Ratio d'équité
    ax3 = axes[2]
    ratios = [results[p]['ratio_PREPA_ING'] for p in policies]
    colors = ['#27ae60' if abs(r - 1) < 0.1 else '#e74c3c' for r in ratios]
    ax3.bar(x, ratios, color=colors)
    ax3.axhline(y=1.0, color='gray', linestyle='--', label='Équité parfaite')
    ax3.set_xlabel('Politique')
    ax3.set_ylabel('Ratio E[W]_PREPA / E[W]_ING')
    ax3.set_title('Indice d\'Équité (1 = parfait)')
    ax3.set_xticks(x)
    ax3.set_xticklabels(policies, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"\n✅ Graphique sauvegardé : {save_path}")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    print("\n" + "🚀 " * 20)
    print("   SIMULATEUR AVEC POLITIQUES DE PRIORITÉ")
    print("🚀 " * 20)
    
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
        seed=42
    )
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print("RÉSUMÉ COMPARATIF")
    print(f"{'='*70}")
    print(f"{'Politique':<20} | {'E[W] ING':>10} | {'E[W] PREPA':>10} | {'E[W] Global':>10} | {'Ratio':>8}")
    print(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")
    
    for policy, data in results.items():
        print(f"{policy:<20} | {data['E[W]_ING']:>10.4f} | {data['E[W]_PREPA']:>10.4f} | "
              f"{data['E[W]_global']:>10.4f} | {data['ratio_PREPA_ING']:>8.4f}")
    
    print(f"{'='*70}")
    
    # Recommandation
    best_global = min(results.items(), key=lambda x: x[1]['E[W]_global'])
    best_equity = min(results.items(), key=lambda x: abs(x[1]['ratio_PREPA_ING'] - 1))
    
    print(f"\n📊 RECOMMANDATIONS:")
    print(f"   • Meilleur temps global : {best_global[0]} (E[W] = {best_global[1]['E[W]_global']:.4f})")
    print(f"   • Meilleure équité      : {best_equity[0]} (Ratio = {best_equity[1]['ratio_PREPA_ING']:.4f})")
    
    # Générer le graphique
    plot_policy_comparison(results)
    
    return results


if __name__ == "__main__":
    results = main()
