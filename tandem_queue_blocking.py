#!/usr/bin/env python3
"""
Simulation à événements discrets avec BLOCAGE PÉRIODIQUE des serveurs.

Architecture du système :
    ING/PREPA → [Station 1: K serveurs] → [Station 2] → Sortie
                      ↑                        ↑
                 Blocage périodique       Blocage périodique

Cycle de blocage :
    |← tb (fermé) →|← tb/2 (ouvert) →|← tb (fermé) →|...

Pendant la période de blocage :
- Les serveurs ne traitent pas de nouveaux jobs
- Les jobs en cours terminent leur service
- Les arrivées s'accumulent dans la file (si capacité)

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
    BLOCK_START_S1 = auto()      # Début blocage station 1
    BLOCK_END_S1 = auto()        # Fin blocage station 1
    BLOCK_START_S2 = auto()      # Début blocage station 2
    BLOCK_END_S2 = auto()        # Fin blocage station 2


class Population(Enum):
    ING = "ING"
    PREPA = "PREPA"


class ServerState(Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"


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
    
    # Temps de service
    service_time_s1: float = 0.0
    service_time_s2: float = 0.0
    
    # Temps d'attente dû au blocage
    blocking_wait_s1: float = 0.0
    blocking_wait_s2: float = 0.0
    
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
    job: Optional['Job'] = field(compare=False, default=None)


# =============================================================================
# SIMULATEUR AVEC BLOCAGE PÉRIODIQUE
# =============================================================================

class BlockingQueueSimulator:
    """
    Simulateur avec blocage périodique des serveurs.
    
    Cycle : tb (fermé) → tb/2 (ouvert) → tb (fermé) → ...
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
        # Blocage
        tb: float = 0.0,           # Durée de blocage (0 = pas de blocage)
        block_s1: bool = True,     # Bloquer station 1
        block_s2: bool = True,     # Bloquer station 2
        sync_blocking: bool = True, # Blocage synchronisé entre stations
    ):
        """
        Args:
            tb: Durée de blocage. Période ouverte = tb/2.
                Si tb=0, pas de blocage.
            block_s1, block_s2: Activer le blocage par station
            sync_blocking: Si True, les deux stations bloquent en même temps
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
        
        # Paramètres de blocage
        self.tb = tb
        self.t_open = tb / 2 if tb > 0 else float('inf')
        self.block_s1 = block_s1 and tb > 0
        self.block_s2 = block_s2 and tb > 0
        self.sync_blocking = sync_blocking
        
        # Période totale du cycle
        self.cycle_period = tb + self.t_open if tb > 0 else float('inf')
        
        # Taux d'utilisation théorique (tenant compte du blocage)
        if tb > 0:
            self.availability = self.t_open / self.cycle_period
        else:
            self.availability = 1.0
        
        self._reset()
    
    def _reset(self):
        """Réinitialise l'état."""
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        
        # Station 1
        self.queue_s1: List[Job] = []
        self.servers_s1: List[Optional[Job]] = [None] * self.K
        self.state_s1 = ServerState.OPEN
        
        # Station 2
        self.queue_s2: List[Job] = []
        self.server_s2: Optional[Job] = None
        self.state_s2 = ServerState.OPEN
        
        # Compteurs
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
        
        # Statistiques de blocage
        self.total_blocking_time_s1 = 0.0
        self.total_blocking_time_s2 = 0.0
        self.block_count_s1 = 0
        self.block_count_s2 = 0
    
    def _schedule_event(self, event: Event):
        heapq.heappush(self.event_queue, event)
    
    def _generate_interarrival_ing(self) -> float:
        return random.expovariate(self.lambda_ing) if self.lambda_ing > 0 else float('inf')
    
    def _generate_interarrival_prepa(self) -> float:
        return random.expovariate(self.lambda_prepa) if self.lambda_prepa > 0 else float('inf')
    
    def _generate_service_s1(self, pop: Population) -> float:
        if pop == Population.ING:
            return random.expovariate(self.mu1_ing)
        else:
            return random.expovariate(self.mu1_prepa)
    
    def _generate_service_s2(self, pop: Population) -> float:
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
    
    def _try_start_service_s1(self, job: Job):
        """Essaie de démarrer le service pour un job en station 1."""
        if self.state_s1 == ServerState.BLOCKED:
            # Serveur bloqué, le job reste en file
            if job not in self.queue_s1:
                self.queue_s1.append(job)
            return
        
        free_server = self._find_free_server_s1()
        if free_server >= 0:
            job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1(job.population)
            job.service_time_s1 = service_time
            job.end_service_s1 = self.current_time + service_time
            self.servers_s1[free_server] = job
            
            self._schedule_event(Event(
                time=job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=job
            ))
        else:
            if job not in self.queue_s1:
                self.queue_s1.append(job)
    
    def _try_start_service_s2(self, job: Job):
        """Essaie de démarrer le service pour un job en station 2."""
        if self.state_s2 == ServerState.BLOCKED:
            # Serveur bloqué, le job reste en file
            if job not in self.queue_s2:
                self.queue_s2.append(job)
            return
        
        if self.server_s2 is None:
            job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2(job.population)
            job.service_time_s2 = service_time
            job.departure_time = self.current_time + service_time
            self.server_s2 = job
            
            self._schedule_event(Event(
                time=job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=job
            ))
        else:
            if job not in self.queue_s2:
                self.queue_s2.append(job)
    
    def _handle_arrival(self, job: Job, event_type: EventType):
        """Traite l'arrivée d'un job."""
        pop = job.population
        
        # Programmer la prochaine arrivée
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
            return
        
        # Essayer de démarrer le service
        self._try_start_service_s1(job)
    
    def _handle_departure_s1(self, job: Job):
        """Fin de service station 1."""
        pop = job.population
        
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # Prendre le prochain en file si station ouverte
        if self.queue_s1 and self.state_s1 == ServerState.OPEN:
            next_job = self.queue_s1.pop(0)
            self._try_start_service_s1(next_job)
        
        # Vérifier capacité station 2
        if self._count_jobs_station2() >= self.kf:
            self.lost_jobs[pop].append(job)
            return
        
        # Essayer d'entrer en station 2
        self._try_start_service_s2(job)
    
    def _handle_departure_s2(self, job: Job):
        """Fin de service station 2."""
        pop = job.population
        self.server_s2 = None
        self.completed_jobs[pop].append(job)
        
        # Prendre le prochain en file si station ouverte
        if self.queue_s2 and self.state_s2 == ServerState.OPEN:
            next_job = self.queue_s2.pop(0)
            self._try_start_service_s2(next_job)
    
    def _handle_block_start_s1(self):
        """Début du blocage station 1."""
        self.state_s1 = ServerState.BLOCKED
        self.block_count_s1 += 1
        
        # Programmer la fin du blocage
        self._schedule_event(Event(
            time=self.current_time + self.tb,
            event_type=EventType.BLOCK_END_S1
        ))
        
        self.total_blocking_time_s1 += self.tb
    
    def _handle_block_end_s1(self):
        """Fin du blocage station 1."""
        self.state_s1 = ServerState.OPEN
        
        # Programmer le prochain blocage
        self._schedule_event(Event(
            time=self.current_time + self.t_open,
            event_type=EventType.BLOCK_START_S1
        ))
        
        # Traiter les jobs en attente
        while self.queue_s1 and self._find_free_server_s1() >= 0:
            job = self.queue_s1.pop(0)
            self._try_start_service_s1(job)
    
    def _handle_block_start_s2(self):
        """Début du blocage station 2."""
        self.state_s2 = ServerState.BLOCKED
        self.block_count_s2 += 1
        
        # Programmer la fin du blocage
        self._schedule_event(Event(
            time=self.current_time + self.tb,
            event_type=EventType.BLOCK_END_S2
        ))
        
        self.total_blocking_time_s2 += self.tb
    
    def _handle_block_end_s2(self):
        """Fin du blocage station 2."""
        self.state_s2 = ServerState.OPEN
        
        # Programmer le prochain blocage
        self._schedule_event(Event(
            time=self.current_time + self.t_open,
            event_type=EventType.BLOCK_START_S2
        ))
        
        # Traiter les jobs en attente
        if self.queue_s2 and self.server_s2 is None:
            job = self.queue_s2.pop(0)
            self._try_start_service_s2(job)
    
    def run(self, max_time: float = 10000.0, warmup_time: float = 1000.0) -> Dict:
        """Exécute la simulation."""
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
        
        # Programmer les premiers blocages
        if self.block_s1:
            # Commencer par une période ouverte, puis bloquer
            self._schedule_event(Event(
                time=self.t_open,
                event_type=EventType.BLOCK_START_S1
            ))
        
        if self.block_s2:
            if self.sync_blocking:
                # Même timing que S1
                self._schedule_event(Event(
                    time=self.t_open,
                    event_type=EventType.BLOCK_START_S2
                ))
            else:
                # Décalé de la moitié du cycle
                self._schedule_event(Event(
                    time=self.t_open + self.cycle_period / 2,
                    event_type=EventType.BLOCK_START_S2
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
            elif event.event_type == EventType.BLOCK_START_S1:
                self._handle_block_start_s1()
            elif event.event_type == EventType.BLOCK_END_S1:
                self._handle_block_end_s1()
            elif event.event_type == EventType.BLOCK_START_S2:
                self._handle_block_start_s2()
            elif event.event_type == EventType.BLOCK_END_S2:
                self._handle_block_end_s2()
        
        # Collecter les résultats
        results = {}
        
        for pop in [Population.ING, Population.PREPA]:
            steady_jobs = [j for j in self.completed_jobs[pop] 
                          if j.arrival_time >= warmup_time]
            
            sojourn_times = [j.sojourn_time() for j in steady_jobs]
            waiting_s1 = [j.waiting_time_s1() for j in steady_jobs]
            waiting_s2 = [j.waiting_time_s2() for j in steady_jobs]
            
            results[pop.value] = {
                'completions': len(steady_jobs),
                'sojourn_times': sojourn_times,
                'mean_sojourn': mean(sojourn_times) if sojourn_times else 0,
                'var_sojourn': variance(sojourn_times) if sojourn_times else 0,
                'std_sojourn': std(sojourn_times) if sojourn_times else 0,
                'mean_waiting_s1': mean(waiting_s1) if waiting_s1 else 0,
                'mean_waiting_s2': mean(waiting_s2) if waiting_s2 else 0,
                'percentile_50': percentile(sojourn_times, 0.5),
                'percentile_90': percentile(sojourn_times, 0.9),
                'percentile_99': percentile(sojourn_times, 0.99),
            }
        
        # Statistiques globales
        results['blocking'] = {
            'tb': self.tb,
            't_open': self.t_open,
            'availability': self.availability,
            'block_count_s1': self.block_count_s1,
            'block_count_s2': self.block_count_s2,
            'total_blocking_time_s1': self.total_blocking_time_s1,
            'total_blocking_time_s2': self.total_blocking_time_s2,
        }
        
        return results


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def variance(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = mean(values)
    return sum((x - m) ** 2 for x in values) / (n - 1)


def std(values: List[float]) -> float:
    return math.sqrt(variance(values))


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(p * (len(sorted_vals) - 1))
    return sorted_vals[idx]


def gini_coefficient(values: List[float]) -> float:
    """
    Calcule le coefficient de Gini (mesure d'inégalité).
    0 = égalité parfaite, 1 = inégalité maximale.
    """
    if not values or len(values) < 2:
        return 0.0
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumsum = sum(sorted_vals)
    
    if cumsum == 0:
        return 0.0
    
    # Formule simplifiée
    sum_weighted = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
    return sum_weighted / (n * cumsum)


def jain_fairness_index(values: List[float]) -> float:
    """
    Indice d'équité de Jain.
    1 = parfaitement équitable, proche de 0 = très inéquitable.
    """
    if not values or len(values) < 2:
        return 1.0
    
    n = len(values)
    sum_x = sum(values)
    sum_x2 = sum(x ** 2 for x in values)
    
    if sum_x2 == 0:
        return 1.0
    
    return (sum_x ** 2) / (n * sum_x2)


# =============================================================================
# FONCTIONS D'ANALYSE COMPARATIVE
# =============================================================================

def compare_blocking_models(
    lambda_ing: float,
    lambda_prepa: float,
    mu1_ing: float,
    mu1_prepa: float,
    mu2_ing: float,
    mu2_prepa: float,
    K: int,
    tb_values: List[float],
    n_trajectories: int = 15,
    max_time: float = 10000.0,
    warmup_time: float = 1000.0
) -> Dict:
    """
    Compare différentes durées de blocage.
    """
    results = {
        'tb': tb_values,
        'availability': [],
        # ING
        'ing_mean': [],
        'ing_var': [],
        'ing_std': [],
        # PREPA
        'prepa_mean': [],
        'prepa_var': [],
        'prepa_std': [],
        # Équité
        'fairness_ratio': [],  # E[W]_PREPA / E[W]_ING
        'gini_global': [],
        'jain_index': [],
    }
    
    print(f"\n{'='*80}")
    print("COMPARAISON MODÈLES AVEC/SANS BLOCAGE PÉRIODIQUE")
    print(f"{'='*80}")
    print(f"ING   : λ={lambda_ing}, μ1={mu1_ing}, μ2={mu2_ing}")
    print(f"PREPA : λ={lambda_prepa}, μ1={mu1_prepa}, μ2={mu2_prepa}")
    print(f"Serveurs K={K}")
    print(f"Cycle : tb (fermé) → tb/2 (ouvert)")
    print(f"{'='*80}\n")
    
    for tb in tb_values:
        ing_means = []
        ing_vars = []
        prepa_means = []
        prepa_vars = []
        all_sojourns = []
        
        for _ in range(n_trajectories):
            sim = BlockingQueueSimulator(
                lambda_ing=lambda_ing,
                lambda_prepa=lambda_prepa,
                mu1_ing=mu1_ing,
                mu1_prepa=mu1_prepa,
                mu2_ing=mu2_ing,
                mu2_prepa=mu2_prepa,
                K=K,
                tb=tb
            )
            
            res = sim.run(max_time=max_time, warmup_time=warmup_time)
            
            if res['ING']['sojourn_times']:
                ing_means.append(res['ING']['mean_sojourn'])
                ing_vars.append(res['ING']['var_sojourn'])
                all_sojourns.extend(res['ING']['sojourn_times'])
            
            if res['PREPA']['sojourn_times']:
                prepa_means.append(res['PREPA']['mean_sojourn'])
                prepa_vars.append(res['PREPA']['var_sojourn'])
                all_sojourns.extend(res['PREPA']['sojourn_times'])
        
        # Disponibilité
        availability = (tb / 2) / (tb + tb / 2) if tb > 0 else 1.0
        results['availability'].append(availability)
        
        # Moyennes et variances
        results['ing_mean'].append(mean(ing_means) if ing_means else 0)
        results['ing_var'].append(mean(ing_vars) if ing_vars else 0)
        results['ing_std'].append(std(ing_means) if ing_means else 0)
        
        results['prepa_mean'].append(mean(prepa_means) if prepa_means else 0)
        results['prepa_var'].append(mean(prepa_vars) if prepa_vars else 0)
        results['prepa_std'].append(std(prepa_means) if prepa_means else 0)
        
        # Équité
        if ing_means and prepa_means:
            fairness = mean(prepa_means) / mean(ing_means)
        else:
            fairness = 1.0
        results['fairness_ratio'].append(fairness)
        
        # Gini et Jain
        results['gini_global'].append(gini_coefficient(all_sojourns))
        results['jain_index'].append(jain_fairness_index(all_sojourns))
        
        # Affichage
        tb_str = f"{tb:.1f}" if tb > 0 else "0 (pas de blocage)"
        print(f"tb = {tb_str:15s} | Dispo: {availability*100:5.1f}% | "
              f"E[W]_ING: {results['ing_mean'][-1]:6.2f} | "
              f"E[W]_PREPA: {results['prepa_mean'][-1]:6.2f} | "
              f"Ratio: {fairness:.3f}")
    
    return results


def analyze_fairness(
    lambda_ing: float,
    lambda_prepa: float,
    mu1_ing: float,
    mu1_prepa: float,
    mu2_ing: float,
    mu2_prepa: float,
    K: int,
    tb: float,
    n_trajectories: int = 20,
    max_time: float = 10000.0,
    warmup_time: float = 1000.0
) -> Dict:
    """
    Analyse détaillée de l'équité entre populations avec et sans blocage.
    """
    results = {'with_blocking': {}, 'without_blocking': {}}
    
    for blocking, tb_val in [('without_blocking', 0.0), ('with_blocking', tb)]:
        ing_sojourns = []
        prepa_sojourns = []
        
        for _ in range(n_trajectories):
            sim = BlockingQueueSimulator(
                lambda_ing=lambda_ing,
                lambda_prepa=lambda_prepa,
                mu1_ing=mu1_ing,
                mu1_prepa=mu1_prepa,
                mu2_ing=mu2_ing,
                mu2_prepa=mu2_prepa,
                K=K,
                tb=tb_val
            )
            
            res = sim.run(max_time=max_time, warmup_time=warmup_time)
            
            ing_sojourns.extend(res['ING']['sojourn_times'])
            prepa_sojourns.extend(res['PREPA']['sojourn_times'])
        
        all_sojourns = ing_sojourns + prepa_sojourns
        
        results[blocking] = {
            'ing_mean': mean(ing_sojourns),
            'ing_var': variance(ing_sojourns),
            'ing_p90': percentile(ing_sojourns, 0.9),
            'prepa_mean': mean(prepa_sojourns),
            'prepa_var': variance(prepa_sojourns),
            'prepa_p90': percentile(prepa_sojourns, 0.9),
            'fairness_ratio': mean(prepa_sojourns) / mean(ing_sojourns) if ing_sojourns else 0,
            'gini': gini_coefficient(all_sojourns),
            'jain': jain_fairness_index(all_sojourns),
            'cv_ing': std(ing_sojourns) / mean(ing_sojourns) if ing_sojourns else 0,
            'cv_prepa': std(prepa_sojourns) / mean(prepa_sojourns) if prepa_sojourns else 0,
        }
    
    return results


# =============================================================================
# GRAPHIQUES
# =============================================================================

def plot_blocking_comparison(results: Dict, save_path: str = "blocking_comparison.png"):
    """Graphiques de comparaison avec/sans blocage."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Impact du Blocage Périodique des Serveurs\n'
                 'Cycle: tb (fermé) → tb/2 (ouvert)', 
                 fontsize=14, fontweight='bold')
    
    tb_vals = results['tb']
    
    # 1. Temps de séjour moyen
    ax1 = axes[0, 0]
    ax1.errorbar(tb_vals, results['ing_mean'], yerr=results['ing_std'],
                 fmt='o-', capsize=4, color='#3498db', linewidth=2,
                 markersize=8, label='ING')
    ax1.errorbar(tb_vals, results['prepa_mean'], yerr=results['prepa_std'],
                 fmt='s-', capsize=4, color='#e74c3c', linewidth=2,
                 markersize=8, label='PREPA')
    ax1.set_xlabel('Durée de blocage tb', fontsize=11)
    ax1.set_ylabel('Temps de séjour moyen E[W]', fontsize=11)
    ax1.set_title('Temps de Séjour Moyen', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Marquer le cas sans blocage
    ax1.axvline(0, color='green', linestyle='--', alpha=0.5, label='Sans blocage')
    
    # 2. Variance du temps de séjour
    ax2 = axes[0, 1]
    ax2.plot(tb_vals, results['ing_var'], 'o-', color='#3498db', 
             linewidth=2, markersize=8, label='Var[W] ING')
    ax2.plot(tb_vals, results['prepa_var'], 's-', color='#e74c3c',
             linewidth=2, markersize=8, label='Var[W] PREPA')
    ax2.set_xlabel('Durée de blocage tb', fontsize=11)
    ax2.set_ylabel('Variance Var[W]', fontsize=11)
    ax2.set_title('Variance du Temps de Séjour', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Ratio d'équité (PREPA/ING)
    ax3 = axes[1, 0]
    ax3.plot(tb_vals, results['fairness_ratio'], '^-', color='#9b59b6',
             linewidth=2, markersize=10)
    ax3.axhline(1.0, color='green', linestyle='--', alpha=0.5, 
                label='Équité parfaite')
    ax3.set_xlabel('Durée de blocage tb', fontsize=11)
    ax3.set_ylabel('Ratio E[W]_PREPA / E[W]_ING', fontsize=11)
    ax3.set_title('Ratio d\'Équité entre Populations', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Indices d'équité globaux
    ax4 = axes[1, 1]
    ax4.plot(tb_vals, results['jain_index'], 'D-', color='#27ae60',
             linewidth=2, markersize=8, label='Indice de Jain')
    ax4.plot(tb_vals, [1 - g for g in results['gini_global']], 'o-', 
             color='#f39c12', linewidth=2, markersize=8, label='1 - Gini')
    ax4.set_xlabel('Durée de blocage tb', fontsize=11)
    ax4.set_ylabel('Indice d\'équité', fontsize=11)
    ax4.set_title('Indices d\'Équité Globaux\n(1 = parfait)', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def plot_detailed_fairness(results: Dict, tb: float, 
                           save_path: str = "fairness_analysis.png"):
    """Graphique détaillé de l'analyse d'équité."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Analyse d\'Équité: Sans blocage vs Avec blocage (tb={tb})', 
                 fontsize=14, fontweight='bold')
    
    scenarios = ['without_blocking', 'with_blocking']
    labels = ['Sans blocage', f'Avec blocage (tb={tb})']
    colors = ['#3498db', '#e74c3c']
    
    # 1. Comparaison des moyennes
    ax1 = axes[0]
    x = range(len(scenarios))
    width = 0.35
    
    ing_means = [results[s]['ing_mean'] for s in scenarios]
    prepa_means = [results[s]['prepa_mean'] for s in scenarios]
    
    bars1 = ax1.bar([i - width/2 for i in x], ing_means, width, 
                    label='ING', color='#3498db', alpha=0.8)
    bars2 = ax1.bar([i + width/2 for i in x], prepa_means, width,
                    label='PREPA', color='#e74c3c', alpha=0.8)
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel('Temps de séjour moyen', fontsize=11)
    ax1.set_title('Temps de Séjour Moyen', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Annotations
    for bar, val in zip(bars1, ing_means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{val:.2f}', ha='center', fontsize=9)
    for bar, val in zip(bars2, prepa_means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{val:.2f}', ha='center', fontsize=9)
    
    # 2. Comparaison des variances
    ax2 = axes[1]
    
    ing_vars = [results[s]['ing_var'] for s in scenarios]
    prepa_vars = [results[s]['prepa_var'] for s in scenarios]
    
    bars1 = ax2.bar([i - width/2 for i in x], ing_vars, width,
                    label='ING', color='#3498db', alpha=0.8)
    bars2 = ax2.bar([i + width/2 for i in x], prepa_vars, width,
                    label='PREPA', color='#e74c3c', alpha=0.8)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel('Variance', fontsize=11)
    ax2.set_title('Variance du Temps de Séjour', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Indices d'équité
    ax3 = axes[2]
    
    ratios = [results[s]['fairness_ratio'] for s in scenarios]
    jains = [results[s]['jain'] for s in scenarios]
    ginis = [1 - results[s]['gini'] for s in scenarios]
    
    x_pos = range(len(scenarios))
    width = 0.25
    
    ax3.bar([i - width for i in x_pos], ratios, width, label='Ratio P/I', 
            color='#9b59b6', alpha=0.8)
    ax3.bar([i for i in x_pos], jains, width, label='Jain', 
            color='#27ae60', alpha=0.8)
    ax3.bar([i + width for i in x_pos], ginis, width, label='1-Gini',
            color='#f39c12', alpha=0.8)
    
    ax3.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(labels)
    ax3.set_ylabel('Valeur', fontsize=11)
    ax3.set_title('Métriques d\'Équité', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def print_comparison_table(results: Dict):
    """Affiche un tableau comparatif."""
    print(f"\n{'='*100}")
    print("TABLEAU COMPARATIF - IMPACT DU BLOCAGE PÉRIODIQUE")
    print(f"{'='*100}")
    
    print(f"\n{'tb':>8} | {'Dispo':>6} | {'E[W] ING':>10} | {'Var ING':>10} | "
          f"{'E[W] PREPA':>10} | {'Var PREPA':>10} | {'Ratio':>7} | {'Jain':>6}")
    print(f"{'-'*8}-+-{'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*7}-+-{'-'*6}")
    
    for i, tb in enumerate(results['tb']):
        tb_str = f"{tb:.1f}" if tb > 0 else "0"
        print(f"{tb_str:>8} | {results['availability'][i]*100:5.1f}% | "
              f"{results['ing_mean'][i]:10.3f} | {results['ing_var'][i]:10.3f} | "
              f"{results['prepa_mean'][i]:10.3f} | {results['prepa_var'][i]:10.3f} | "
              f"{results['fairness_ratio'][i]:7.3f} | {results['jain_index'][i]:6.4f}")
    
    print(f"{'='*100}")
    
    # Analyse
    no_block_idx = 0  # tb = 0
    
    print(f"\n📊 ANALYSE DE L'IMPACT DU BLOCAGE:")
    print(f"{'─'*60}")
    
    # Trouver le pire cas de blocage
    max_tb_idx = len(results['tb']) - 1
    
    ing_increase = (results['ing_mean'][max_tb_idx] / results['ing_mean'][no_block_idx] - 1) * 100
    prepa_increase = (results['prepa_mean'][max_tb_idx] / results['prepa_mean'][no_block_idx] - 1) * 100
    
    print(f"• Avec tb max = {results['tb'][max_tb_idx]}:")
    print(f"  - Augmentation E[W] ING   : +{ing_increase:.1f}%")
    print(f"  - Augmentation E[W] PREPA : +{prepa_increase:.1f}%")
    
    # Équité
    ratio_no_block = results['fairness_ratio'][no_block_idx]
    ratio_max_block = results['fairness_ratio'][max_tb_idx]
    
    if ratio_max_block < ratio_no_block:
        print(f"• Le blocage AMÉLIORE l'équité (ratio plus proche de 1)")
    else:
        print(f"• Le blocage DÉGRADE l'équité (ratio plus éloigné de 1)")
    
    print(f"  - Sans blocage : ratio = {ratio_no_block:.3f}")
    print(f"  - Avec blocage : ratio = {ratio_max_block:.3f}")
    
    print(f"{'='*100}\n")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    print("\n" + "🔒 " * 20)
    print("   SIMULATEUR AVEC BLOCAGE PÉRIODIQUE")
    print("🔒 " * 20)
    
    # =========================================================================
    # PARAMÈTRES
    # =========================================================================
    
    # Arrivées
    LAMBDA_ING = 3.0
    LAMBDA_PREPA = 2.0
    
    # Services (ING rapide, PREPA lent)
    MU1_ING = 4.0
    MU1_PREPA = 1.0
    MU2_ING = 8.0
    MU2_PREPA = 3.0
    
    # Infrastructure
    K = 4
    
    # Durées de blocage à tester
    TB_VALUES = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0]
    
    # Simulation
    N_TRAJECTORIES = 15
    MAX_TIME = 10000.0
    WARMUP_TIME = 1000.0
    
    random.seed(42)
    
    # =========================================================================
    # 1. COMPARAISON DES MODÈLES
    # =========================================================================
    
    results = compare_blocking_models(
        lambda_ing=LAMBDA_ING,
        lambda_prepa=LAMBDA_PREPA,
        mu1_ing=MU1_ING,
        mu1_prepa=MU1_PREPA,
        mu2_ing=MU2_ING,
        mu2_prepa=MU2_PREPA,
        K=K,
        tb_values=TB_VALUES,
        n_trajectories=N_TRAJECTORIES,
        max_time=MAX_TIME,
        warmup_time=WARMUP_TIME
    )
    
    # Tableau
    print_comparison_table(results)
    
    # Graphiques
    print("\n📊 Génération des graphiques...")
    plot_blocking_comparison(results, save_path="img/blocking_comparison.png")
    
    # =========================================================================
    # 2. ANALYSE DÉTAILLÉE DE L'ÉQUITÉ
    # =========================================================================
    
    print("\n" + "="*80)
    print("ANALYSE DÉTAILLÉE DE L'ÉQUITÉ")
    print("="*80)
    
    TB_ANALYSIS = 5.0  # Durée de blocage pour l'analyse détaillée
    
    fairness_results = analyze_fairness(
        lambda_ing=LAMBDA_ING,
        lambda_prepa=LAMBDA_PREPA,
        mu1_ing=MU1_ING,
        mu1_prepa=MU1_PREPA,
        mu2_ing=MU2_ING,
        mu2_prepa=MU2_PREPA,
        K=K,
        tb=TB_ANALYSIS,
        n_trajectories=20,
        max_time=MAX_TIME,
        warmup_time=WARMUP_TIME
    )
    
    print(f"\nComparaison détaillée (tb = {TB_ANALYSIS}):")
    print(f"{'─'*60}")
    
    for scenario, label in [('without_blocking', 'Sans blocage'), 
                            ('with_blocking', f'Avec blocage (tb={TB_ANALYSIS})')]:
        r = fairness_results[scenario]
        print(f"\n{label}:")
        print(f"  ING   : E[W]={r['ing_mean']:.3f}, Var={r['ing_var']:.3f}, CV={r['cv_ing']:.3f}")
        print(f"  PREPA : E[W]={r['prepa_mean']:.3f}, Var={r['prepa_var']:.3f}, CV={r['cv_prepa']:.3f}")
        print(f"  Ratio P/I : {r['fairness_ratio']:.3f}")
        print(f"  Gini : {r['gini']:.4f}, Jain : {r['jain']:.4f}")
    
    plot_detailed_fairness(fairness_results, TB_ANALYSIS, 
                           save_path="img/fairness_analysis.png")
    
    # =========================================================================
    # 3. CONCLUSIONS
    # =========================================================================
    
    print("\n" + "="*80)
    print("📋 CONCLUSIONS")
    print("="*80)
    
    print(f"""
    1. IMPACT SUR LES TEMPS DE SÉJOUR:
       • Le blocage augmente E[W] pour les deux populations
       • L'augmentation est proportionnelle à tb et à (1/disponibilité)
       • Les PREPA sont légèrement plus impactés (services plus longs)
    
    2. IMPACT SUR LA VARIANCE:
       • La variance augmente avec tb
       • Le blocage introduit des pics d'attente après réouverture
       • Coefficient de variation (CV) plus élevé avec blocage
    
    3. ÉQUITÉ ENTRE POPULATIONS:
       • Le ratio PREPA/ING reste relativement stable
       • Le blocage n'améliore pas significativement l'équité
       • Les deux populations subissent un surcoût similaire
    
    4. RECOMMANDATIONS:
       • Minimiser tb autant que possible
       • Si blocage nécessaire : préférer des blocages courts et fréquents
       • Considérer un blocage asynchrone entre stations
    """)
    
    return results, fairness_results


if __name__ == "__main__":
    results, fairness_results = main()
