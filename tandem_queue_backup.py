#!/usr/bin/env python3
"""
Simulation à événements discrets avec mécanisme de BACK-UP.

Architecture du système :
    Arrivées → [Station 1: M/M/K/ks] → [Backup?] → [Station 2: M/M/1/kf] → Sortie

Mécanismes de back-up :
1. SYSTÉMATIQUE : tous les jobs sont sauvegardés après station 1
2. ALÉATOIRE : chaque job a une probabilité p d'être sauvegardé

Avantage du back-up :
- Si un job est perdu (station 2 pleine), il peut être récupéré depuis le backup
- Évite les "pages blanches" (résultats indisponibles)

Coût du back-up :
- Temps de sauvegarde (latence additionnelle)
- Espace de stockage utilisé

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
    ARRIVAL = auto()
    DEPARTURE_STATION1 = auto()
    BACKUP_COMPLETE = auto()      # Nouveau : fin de sauvegarde
    DEPARTURE_STATION2 = auto()
    RETRY_FROM_BACKUP = auto()    # Nouveau : réessai depuis le backup


class JobStatus(Enum):
    COMPLETED = auto()
    REJECTED = auto()
    LOST_NO_BACKUP = auto()       # Perdu sans backup = page blanche
    RECOVERED_FROM_BACKUP = auto() # Récupéré depuis le backup


class BackupMode(Enum):
    NONE = auto()          # Pas de backup
    SYSTEMATIC = auto()    # Backup systématique (tous les jobs)
    RANDOM = auto()        # Backup aléatoire (probabilité p)


@dataclass
class Job:
    """Représente un job avec informations de backup."""
    job_id: int
    arrival_time: float
    status: JobStatus = JobStatus.COMPLETED
    
    # Timestamps
    start_service_s1: Optional[float] = None
    end_service_s1: Optional[float] = None
    backup_start: Optional[float] = None
    backup_end: Optional[float] = None
    start_service_s2: Optional[float] = None
    departure_time: Optional[float] = None
    
    # Backup info
    has_backup: bool = False
    was_lost_initially: bool = False
    retry_count: int = 0
    
    def sojourn_time(self) -> float:
        """Temps de séjour total."""
        if self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return float('inf')
    
    def backup_latency(self) -> float:
        """Latence due au backup."""
        if self.backup_end is not None and self.backup_start is not None:
            return self.backup_end - self.backup_start
        return 0.0


@dataclass(order=True)
class Event:
    time: float
    event_type: EventType = field(compare=False)
    job: Job = field(compare=False)


# =============================================================================
# SIMULATEUR AVEC BACKUP
# =============================================================================

class BackupQueueSimulator:
    """
    Simulateur avec mécanisme de back-up entre les deux stations.
    
    Le backup se fait APRÈS la station 1, AVANT la station 2.
    Si la station 2 est pleine et que le job a un backup, il peut réessayer.
    """
    
    def __init__(
        self,
        lambda_rate: float,
        mu1: float,
        mu2: float,
        K: int,
        ks: int,
        kf: int,
        backup_mode: BackupMode = BackupMode.NONE,
        backup_prob: float = 0.5,
        backup_time_mean: float = 0.1,
        retry_delay: float = 0.5,
        max_retries: int = 3,
        storage_cost_per_backup: float = 1.0
    ):
        """
        Args:
            lambda_rate: Taux d'arrivée
            mu1, mu2: Taux de service
            K: Serveurs station 1
            ks, kf: Capacités
            backup_mode: Mode de backup (NONE, SYSTEMATIC, RANDOM)
            backup_prob: Probabilité de backup (pour mode RANDOM)
            backup_time_mean: Temps moyen de sauvegarde (exponentiel)
            retry_delay: Délai avant réessai depuis backup
            max_retries: Nombre max de réessais
            storage_cost_per_backup: Coût unitaire de stockage
        """
        self.lambda_rate = lambda_rate
        self.mu1 = mu1
        self.mu2 = mu2
        self.K = K
        self.ks = max(ks, K)
        self.kf = max(kf, 1)
        
        # Paramètres de backup
        self.backup_mode = backup_mode
        self.backup_prob = backup_prob
        self.backup_time_mean = backup_time_mean
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.storage_cost_per_backup = storage_cost_per_backup
        
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
        
        # Backup storage (jobs en attente de réessai ou stockés)
        self.backup_storage: Dict[int, Job] = {}
        self.jobs_in_backup_process: set = set()  # Jobs en cours de backup
        
        # Compteurs
        self.job_counter = 0
        self.completed_jobs: List[Job] = []
        self.rejected_jobs: List[Job] = []
        self.lost_jobs_no_backup: List[Job] = []
        self.recovered_jobs: List[Job] = []
        
        # Statistiques
        self.total_arrivals = 0
        self.total_rejections = 0
        self.total_losses_no_backup = 0  # Pages blanches
        self.total_backups_created = 0
        self.total_storage_used = 0.0
        self.total_backup_time = 0.0
        self.total_recoveries = 0
        self.total_retry_attempts = 0
    
    def _schedule_event(self, event: Event):
        heapq.heappush(self.event_queue, event)
    
    def _generate_interarrival(self) -> float:
        return random.expovariate(self.lambda_rate)
    
    def _generate_service_s1(self) -> float:
        return random.expovariate(self.mu1)
    
    def _generate_service_s2(self) -> float:
        return random.expovariate(self.mu2)
    
    def _generate_backup_time(self) -> float:
        """Temps de backup (exponentiel)."""
        if self.backup_time_mean > 0:
            return random.expovariate(1.0 / self.backup_time_mean)
        return 0.0
    
    def _should_backup(self) -> bool:
        """Détermine si un job doit être sauvegardé."""
        if self.backup_mode == BackupMode.NONE:
            return False
        elif self.backup_mode == BackupMode.SYSTEMATIC:
            return True
        elif self.backup_mode == BackupMode.RANDOM:
            return random.random() < self.backup_prob
        return False
    
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
        
        # Vérifier capacité station 1
        if self._count_jobs_station1() >= self.ks:
            job.status = JobStatus.REJECTED
            self.rejected_jobs.append(job)
            self.total_rejections += 1
            return
        
        # Acceptation
        free_server = self._find_free_server_s1()
        if free_server >= 0:
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
            self.queue_s1.append(job)
    
    def _handle_departure_s1(self, job: Job):
        """Fin de service station 1 -> backup ou station 2."""
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # Prendre le prochain en file
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
        
        # Décider si backup
        if self._should_backup():
            # Démarrer le processus de backup
            job.backup_start = self.current_time
            backup_time = self._generate_backup_time()
            job.backup_end = self.current_time + backup_time
            job.has_backup = True
            self.jobs_in_backup_process.add(job.job_id)
            
            self._schedule_event(Event(
                time=job.backup_end,
                event_type=EventType.BACKUP_COMPLETE,
                job=job
            ))
        else:
            # Pas de backup, aller directement à station 2
            self._try_enter_station2(job)
    
    def _handle_backup_complete(self, job: Job):
        """Fin du backup -> essayer d'entrer en station 2."""
        self.jobs_in_backup_process.discard(job.job_id)
        
        # Enregistrer le backup
        self.backup_storage[job.job_id] = job
        self.total_backups_created += 1
        self.total_storage_used += self.storage_cost_per_backup
        self.total_backup_time += job.backup_latency()
        
        # Essayer d'entrer en station 2
        self._try_enter_station2(job)
    
    def _try_enter_station2(self, job: Job):
        """Tente de faire entrer un job en station 2."""
        if self._count_jobs_station2() >= self.kf:
            # Station 2 pleine
            if job.has_backup:
                # Le job a un backup, on peut réessayer plus tard
                job.was_lost_initially = True
                if job.retry_count < self.max_retries:
                    job.retry_count += 1
                    self.total_retry_attempts += 1
                    
                    # Programmer un réessai
                    self._schedule_event(Event(
                        time=self.current_time + self.retry_delay,
                        event_type=EventType.RETRY_FROM_BACKUP,
                        job=job
                    ))
                else:
                    # Max retries atteint, considéré comme récupéré (donnée disponible)
                    job.status = JobStatus.RECOVERED_FROM_BACKUP
                    job.departure_time = self.current_time
                    self.recovered_jobs.append(job)
                    self.total_recoveries += 1
                    # Nettoyer le backup
                    self.backup_storage.pop(job.job_id, None)
            else:
                # Pas de backup = PAGE BLANCHE
                job.status = JobStatus.LOST_NO_BACKUP
                self.lost_jobs_no_backup.append(job)
                self.total_losses_no_backup += 1
        else:
            # Entrée en station 2
            if self.server_s2 is None:
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
                self.queue_s2.append(job)
            
            # Nettoyer le backup si utilisé
            self.backup_storage.pop(job.job_id, None)
    
    def _handle_retry_from_backup(self, job: Job):
        """Réessai d'entrée en station 2 depuis le backup."""
        # Vérifier que le job est toujours dans le backup
        if job.job_id not in self.backup_storage:
            return
        
        self._try_enter_station2(job)
    
    def _handle_departure_s2(self, job: Job):
        """Fin de service station 2."""
        self.server_s2 = None
        job.status = JobStatus.COMPLETED
        self.completed_jobs.append(job)
        
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
        """Exécute la simulation."""
        self._reset()
        
        # Première arrivée
        first_job = Job(job_id=0, arrival_time=self._generate_interarrival())
        self._schedule_event(Event(
            time=first_job.arrival_time,
            event_type=EventType.ARRIVAL,
            job=first_job
        ))
        
        # Compteurs warmup
        warmup_stats = {}
        warmup_done = False
        
        while self.job_counter < max_jobs and self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if not warmup_done and self.job_counter >= warmup_jobs:
                warmup_done = True
                warmup_stats = {
                    'arrivals': self.total_arrivals,
                    'rejections': self.total_rejections,
                    'losses_no_backup': self.total_losses_no_backup,
                    'backups': self.total_backups_created,
                    'storage': self.total_storage_used,
                    'backup_time': self.total_backup_time,
                    'recoveries': self.total_recoveries,
                }
            
            if event.event_type == EventType.ARRIVAL:
                self._handle_arrival(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION1:
                self._handle_departure_s1(event.job)
            elif event.event_type == EventType.BACKUP_COMPLETE:
                self._handle_backup_complete(event.job)
            elif event.event_type == EventType.RETRY_FROM_BACKUP:
                self._handle_retry_from_backup(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION2:
                self._handle_departure_s2(event.job)
        
        # Calculer les métriques post-warmup
        steady_arrivals = self.total_arrivals - warmup_stats.get('arrivals', 0)
        steady_rejections = self.total_rejections - warmup_stats.get('rejections', 0)
        steady_losses = self.total_losses_no_backup - warmup_stats.get('losses_no_backup', 0)
        steady_backups = self.total_backups_created - warmup_stats.get('backups', 0)
        steady_storage = self.total_storage_used - warmup_stats.get('storage', 0)
        steady_backup_time = self.total_backup_time - warmup_stats.get('backup_time', 0)
        steady_recoveries = self.total_recoveries - warmup_stats.get('recoveries', 0)
        
        # Jobs traités par station 1
        jobs_passed_s1 = steady_arrivals - steady_rejections
        
        # Taux de pages blanches
        blank_page_rate = steady_losses / jobs_passed_s1 if jobs_passed_s1 > 0 else 0
        
        # Jobs complétés après warmup
        steady_completed = [j for j in self.completed_jobs if j.job_id >= warmup_jobs]
        steady_recovered = [j for j in self.recovered_jobs if j.job_id >= warmup_jobs]
        
        # Temps de séjour
        sojourn_times = [j.sojourn_time() for j in steady_completed if j.sojourn_time() < float('inf')]
        backup_latencies = [j.backup_latency() for j in steady_completed if j.has_backup]
        
        # Latence moyenne due au backup
        mean_backup_latency = sum(backup_latencies) / len(backup_latencies) if backup_latencies else 0
        
        return {
            'arrivals': steady_arrivals,
            'rejections': steady_rejections,
            'rejection_rate': steady_rejections / steady_arrivals if steady_arrivals > 0 else 0,
            'losses_no_backup': steady_losses,
            'blank_page_rate': blank_page_rate,
            'backups_created': steady_backups,
            'backup_rate': steady_backups / jobs_passed_s1 if jobs_passed_s1 > 0 else 0,
            'storage_cost': steady_storage,
            'recoveries': steady_recoveries,
            'recovery_rate': steady_recoveries / jobs_passed_s1 if jobs_passed_s1 > 0 else 0,
            'completions': len(steady_completed),
            'mean_sojourn': sum(sojourn_times) / len(sojourn_times) if sojourn_times else 0,
            'var_sojourn': self._variance(sojourn_times) if sojourn_times else 0,
            'mean_backup_latency': mean_backup_latency,
            'total_backup_time': steady_backup_time,
        }
    
    @staticmethod
    def _variance(values: List[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        return sum((x - mean) ** 2 for x in values) / (n - 1)


# =============================================================================
# FONCTIONS DE COMPARAISON
# =============================================================================

def compare_backup_strategies(
    lambda_rate: float,
    mu1: float,
    mu2: float,
    K: int,
    ks: int,
    kf: int,
    backup_probs: List[float],
    backup_time_mean: float = 0.1,
    n_trajectories: int = 10,
    jobs_per_traj: int = 10000,
    warmup: int = 1000
) -> Dict:
    """
    Compare les stratégies de backup pour une valeur de λ donnée.
    
    Args:
        backup_probs: Liste de probabilités [0, 0.25, 0.5, 0.75, 1.0]
                      0 = pas de backup, 1 = systématique
    """
    results = {
        'backup_prob': backup_probs,
        'blank_page_rate_mean': [],
        'blank_page_rate_std': [],
        'storage_cost_mean': [],
        'storage_cost_std': [],
        'sojourn_mean': [],
        'sojourn_std': [],
        'backup_latency_mean': [],
        'recovery_rate_mean': [],
    }
    
    for p in backup_probs:
        if p == 0:
            mode = BackupMode.NONE
        elif p >= 1.0:
            mode = BackupMode.SYSTEMATIC
        else:
            mode = BackupMode.RANDOM
        
        blank_rates = []
        storage_costs = []
        sojourns = []
        backup_latencies = []
        recovery_rates = []
        
        for _ in range(n_trajectories):
            sim = BackupQueueSimulator(
                lambda_rate=lambda_rate,
                mu1=mu1,
                mu2=mu2,
                K=K,
                ks=ks,
                kf=kf,
                backup_mode=mode,
                backup_prob=p,
                backup_time_mean=backup_time_mean
            )
            res = sim.run(max_jobs=jobs_per_traj, warmup_jobs=warmup)
            
            blank_rates.append(res['blank_page_rate'])
            storage_costs.append(res['storage_cost'])
            if res['mean_sojourn'] > 0:
                sojourns.append(res['mean_sojourn'])
            backup_latencies.append(res['mean_backup_latency'])
            recovery_rates.append(res['recovery_rate'])
        
        results['blank_page_rate_mean'].append(mean(blank_rates))
        results['blank_page_rate_std'].append(std(blank_rates))
        results['storage_cost_mean'].append(mean(storage_costs))
        results['storage_cost_std'].append(std(storage_costs))
        results['sojourn_mean'].append(mean(sojourns) if sojourns else 0)
        results['sojourn_std'].append(std(sojourns) if sojourns else 0)
        results['backup_latency_mean'].append(mean(backup_latencies))
        results['recovery_rate_mean'].append(mean(recovery_rates))
    
    return results


def compare_across_lambda(
    lambda_values: List[float],
    mu1: float,
    mu2: float,
    K: int,
    ks: int,
    kf: int,
    backup_time_mean: float = 0.1,
    n_trajectories: int = 10,
    jobs_per_traj: int = 10000,
    warmup: int = 1000
) -> Dict:
    """
    Compare NONE vs SYSTEMATIC vs RANDOM(0.5) pour différentes valeurs de λ.
    """
    strategies = [
        ('Sans backup', BackupMode.NONE, 0.0),
        ('Backup p=0.5', BackupMode.RANDOM, 0.5),
        ('Backup systématique', BackupMode.SYSTEMATIC, 1.0),
    ]
    
    results = {name: {
        'lambda': lambda_values,
        'blank_page_rate': [],
        'storage_cost': [],
        'sojourn': [],
        'latency': [],
    } for name, _, _ in strategies}
    
    print(f"\n{'='*80}")
    print("COMPARAISON DES STRATÉGIES DE BACKUP")
    print(f"{'='*80}")
    print(f"Paramètres: μ1={mu1}, μ2={mu2}, K={K}, ks={ks}, kf={kf}")
    print(f"Temps moyen backup: {backup_time_mean}")
    print(f"{'='*80}\n")
    
    for lam in lambda_values:
        print(f"\n--- λ = {lam} ---")
        
        for name, mode, prob in strategies:
            blank_rates = []
            storage_costs = []
            sojourns = []
            latencies = []
            
            for _ in range(n_trajectories):
                sim = BackupQueueSimulator(
                    lambda_rate=lam,
                    mu1=mu1,
                    mu2=mu2,
                    K=K,
                    ks=ks,
                    kf=kf,
                    backup_mode=mode,
                    backup_prob=prob,
                    backup_time_mean=backup_time_mean
                )
                res = sim.run(max_jobs=jobs_per_traj, warmup_jobs=warmup)
                
                blank_rates.append(res['blank_page_rate'])
                storage_costs.append(res['storage_cost'])
                if res['mean_sojourn'] > 0:
                    sojourns.append(res['mean_sojourn'])
                latencies.append(res['mean_backup_latency'])
            
            results[name]['blank_page_rate'].append(mean(blank_rates))
            results[name]['storage_cost'].append(mean(storage_costs))
            results[name]['sojourn'].append(mean(sojourns) if sojourns else 0)
            results[name]['latency'].append(mean(latencies))
            
            print(f"  {name:25s}: Pages blanches={mean(blank_rates)*100:5.2f}%, "
                  f"Stockage={mean(storage_costs):7.1f}, "
                  f"E[W]={mean(sojourns) if sojourns else 0:6.3f}, "
                  f"Latence backup={mean(latencies):.4f}")
    
    return results


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))


# =============================================================================
# GRAPHIQUES
# =============================================================================

def plot_backup_comparison(results: Dict, save_path: str = "backup_comparison.png"):
    """Génère les graphiques de comparaison des stratégies."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparaison des Stratégies de Backup\n'
                 '(Sans backup vs Aléatoire p=0.5 vs Systématique)', 
                 fontsize=14, fontweight='bold')
    
    colors = {'Sans backup': '#e74c3c', 
              'Backup p=0.5': '#f39c12', 
              'Backup systématique': '#27ae60'}
    markers = {'Sans backup': 'o', 
               'Backup p=0.5': 's', 
               'Backup systématique': '^'}
    
    lambda_vals = list(results.values())[0]['lambda']
    
    # 1. Taux de pages blanches
    ax1 = axes[0, 0]
    for name, data in results.items():
        ax1.plot(lambda_vals, [r * 100 for r in data['blank_page_rate']],
                 marker=markers[name], color=colors[name], 
                 label=name, linewidth=2, markersize=8)
    ax1.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax1.set_ylabel('Taux de pages blanches (%)', fontsize=11)
    ax1.set_title('Taux de Pages Blanches\n(Résultats définitivement perdus)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    # 2. Coût en stockage
    ax2 = axes[0, 1]
    for name, data in results.items():
        ax2.plot(lambda_vals, data['storage_cost'],
                 marker=markers[name], color=colors[name],
                 label=name, linewidth=2, markersize=8)
    ax2.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax2.set_ylabel('Coût de stockage (unités)', fontsize=11)
    ax2.set_title('Coût en Stockage Simulé\n(Backups créés)', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Temps de séjour
    ax3 = axes[1, 0]
    for name, data in results.items():
        ax3.plot(lambda_vals, data['sojourn'],
                 marker=markers[name], color=colors[name],
                 label=name, linewidth=2, markersize=8)
    ax3.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax3.set_ylabel('Temps de séjour E[W]', fontsize=11)
    ax3.set_title('Temps de Séjour Total\n(Jobs complétés)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Latence due au backup
    ax4 = axes[1, 1]
    for name, data in results.items():
        ax4.plot(lambda_vals, data['latency'],
                 marker=markers[name], color=colors[name],
                 label=name, linewidth=2, markersize=8)
    ax4.set_xlabel('Taux d\'arrivée λ', fontsize=11)
    ax4.set_ylabel('Latence moyenne (backup)', fontsize=11)
    ax4.set_title('Latence Induite par le Backup\n(Temps de sauvegarde)', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def plot_probability_analysis(
    lambda_rate: float,
    results: Dict,
    save_path: str = "backup_probability_analysis.png"
):
    """Analyse l'impact de la probabilité de backup."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib non disponible")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Impact de la Probabilité de Backup (λ = {lambda_rate})\n'
                 f'0 = Sans backup, 1 = Systématique', 
                 fontsize=14, fontweight='bold')
    
    probs = results['backup_prob']
    
    # 1. Pages blanches vs probabilité
    ax1 = axes[0, 0]
    ax1.errorbar(probs, [r * 100 for r in results['blank_page_rate_mean']],
                 yerr=[r * 100 for r in results['blank_page_rate_std']],
                 fmt='o-', capsize=4, color='#e74c3c', linewidth=2, markersize=8)
    ax1.fill_between(probs,
                     [(m - s) * 100 for m, s in zip(results['blank_page_rate_mean'], 
                                                     results['blank_page_rate_std'])],
                     [(m + s) * 100 for m, s in zip(results['blank_page_rate_mean'],
                                                     results['blank_page_rate_std'])],
                     alpha=0.2, color='#e74c3c')
    ax1.set_xlabel('Probabilité de backup p', fontsize=11)
    ax1.set_ylabel('Taux de pages blanches (%)', fontsize=11)
    ax1.set_title('Réduction des Pages Blanches', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.05, 1.05)
    ax1.set_ylim(bottom=0)
    
    # 2. Coût stockage vs probabilité
    ax2 = axes[0, 1]
    ax2.errorbar(probs, results['storage_cost_mean'],
                 yerr=results['storage_cost_std'],
                 fmt='s-', capsize=4, color='#3498db', linewidth=2, markersize=8)
    ax2.fill_between(probs,
                     [m - s for m, s in zip(results['storage_cost_mean'],
                                            results['storage_cost_std'])],
                     [m + s for m, s in zip(results['storage_cost_mean'],
                                            results['storage_cost_std'])],
                     alpha=0.2, color='#3498db')
    ax2.set_xlabel('Probabilité de backup p', fontsize=11)
    ax2.set_ylabel('Coût de stockage', fontsize=11)
    ax2.set_title('Coût en Stockage', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(-0.05, 1.05)
    
    # 3. Temps de séjour vs probabilité
    ax3 = axes[1, 0]
    ax3.errorbar(probs, results['sojourn_mean'],
                 yerr=results['sojourn_std'],
                 fmt='^-', capsize=4, color='#27ae60', linewidth=2, markersize=8)
    ax3.fill_between(probs,
                     [m - s for m, s in zip(results['sojourn_mean'],
                                            results['sojourn_std'])],
                     [m + s for m, s in zip(results['sojourn_mean'],
                                            results['sojourn_std'])],
                     alpha=0.2, color='#27ae60')
    ax3.set_xlabel('Probabilité de backup p', fontsize=11)
    ax3.set_ylabel('Temps de séjour E[W]', fontsize=11)
    ax3.set_title('Impact sur le Temps de Séjour', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(-0.05, 1.05)
    
    # 4. Trade-off : Pages blanches vs Coût
    ax4 = axes[1, 1]
    scatter = ax4.scatter(results['storage_cost_mean'],
                          [r * 100 for r in results['blank_page_rate_mean']],
                          c=probs, cmap='RdYlGn', s=150, edgecolors='black')
    for i, p in enumerate(probs):
        ax4.annotate(f'p={p}', 
                     (results['storage_cost_mean'][i], 
                      results['blank_page_rate_mean'][i] * 100),
                     textcoords="offset points", xytext=(5, 5), fontsize=9)
    ax4.set_xlabel('Coût de stockage', fontsize=11)
    ax4.set_ylabel('Taux de pages blanches (%)', fontsize=11)
    ax4.set_title('Trade-off Fiabilité vs Coût', fontsize=12)
    ax4.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Probabilité p')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\n✅ Graphique sauvegardé : {save_path}")


def print_analysis_table(results: Dict):
    """Affiche un tableau d'analyse comparative."""
    print(f"\n{'='*100}")
    print("ANALYSE COMPARATIVE DES STRATÉGIES DE BACKUP")
    print(f"{'='*100}")
    
    strategies = list(results.keys())
    lambda_vals = results[strategies[0]]['lambda']
    
    for lam_idx, lam in enumerate(lambda_vals):
        print(f"\n{'─'*100}")
        print(f"λ = {lam}")
        print(f"{'─'*100}")
        print(f"{'Stratégie':25s} | {'Pages blanches':15s} | {'Stockage':12s} | "
              f"{'E[W]':10s} | {'Latence backup':15s}")
        print(f"{'-'*25}-+-{'-'*15}-+-{'-'*12}-+-{'-'*10}-+-{'-'*15}")
        
        for name in strategies:
            data = results[name]
            blank = data['blank_page_rate'][lam_idx] * 100
            storage = data['storage_cost'][lam_idx]
            sojourn = data['sojourn'][lam_idx]
            latency = data['latency'][lam_idx]
            
            print(f"{name:25s} | {blank:14.2f}% | {storage:12.1f} | "
                  f"{sojourn:10.4f} | {latency:15.4f}")
    
    print(f"\n{'='*100}")
    
    # Résumé
    print("\n📊 RÉSUMÉ:")
    print("─" * 60)
    
    # Réduction des pages blanches (systématique vs sans backup)
    no_backup = results['Sans backup']['blank_page_rate']
    systematic = results['Backup systématique']['blank_page_rate']
    
    avg_reduction = mean([(n - s) / n * 100 if n > 0 else 0 
                          for n, s in zip(no_backup, systematic)])
    print(f"• Réduction moyenne des pages blanches (systématique): {avg_reduction:.1f}%")
    
    # Surcoût en stockage
    storage_systematic = mean(results['Backup systématique']['storage_cost'])
    storage_random = mean(results['Backup p=0.5']['storage_cost'])
    print(f"• Coût moyen stockage - Systématique: {storage_systematic:.1f}")
    print(f"• Coût moyen stockage - Aléatoire p=0.5: {storage_random:.1f}")
    print(f"• Économie avec backup aléatoire: {(1 - storage_random/storage_systematic)*100:.1f}%")
    
    # Latence additionnelle
    latency_systematic = mean(results['Backup systématique']['latency'])
    print(f"• Latence moyenne induite (systématique): {latency_systematic:.4f}")
    
    print(f"{'='*100}\n")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    print("\n" + "🔄 " * 20)
    print("   SIMULATEUR AVEC MÉCANISME DE BACKUP")
    print("🔄 " * 20)
    
    # Paramètres
    MU1 = 2.0
    MU2 = 5.0
    K = 3
    KS = 10
    KF = 5
    BACKUP_TIME_MEAN = 0.1  # Temps moyen de sauvegarde
    
    LAMBDA_VALUES = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    N_TRAJECTORIES = 15
    JOBS_PER_TRAJ = 10000
    WARMUP = 1000
    
    random.seed(42)
    
    # =========================================================================
    # 1. COMPARAISON DES STRATÉGIES POUR DIFFÉRENTES VALEURS DE λ
    # =========================================================================
    
    results_lambda = compare_across_lambda(
        lambda_values=LAMBDA_VALUES,
        mu1=MU1,
        mu2=MU2,
        K=K,
        ks=KS,
        kf=KF,
        backup_time_mean=BACKUP_TIME_MEAN,
        n_trajectories=N_TRAJECTORIES,
        jobs_per_traj=JOBS_PER_TRAJ,
        warmup=WARMUP
    )
    
    # Afficher le tableau
    print_analysis_table(results_lambda)
    
    # Générer les graphiques
    print("\n📊 Génération des graphiques...")
    plot_backup_comparison(results_lambda, save_path="img/backup_comparison.png")
    
    # =========================================================================
    # 2. ANALYSE DE L'IMPACT DE LA PROBABILITÉ p
    # =========================================================================
    
    print("\n" + "="*80)
    print("ANALYSE DE L'IMPACT DE LA PROBABILITÉ DE BACKUP")
    print("="*80)
    
    LAMBDA_FIXED = 6.0  # Charge élevée pour voir les effets
    BACKUP_PROBS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    
    print(f"\nAnalyse pour λ = {LAMBDA_FIXED}")
    
    results_prob = compare_backup_strategies(
        lambda_rate=LAMBDA_FIXED,
        mu1=MU1,
        mu2=MU2,
        K=K,
        ks=KS,
        kf=KF,
        backup_probs=BACKUP_PROBS,
        backup_time_mean=BACKUP_TIME_MEAN,
        n_trajectories=N_TRAJECTORIES,
        jobs_per_traj=JOBS_PER_TRAJ,
        warmup=WARMUP
    )
    
    # Afficher les résultats
    print(f"\n{'p':>5} | {'Pages blanches':>15} | {'Stockage':>12} | "
          f"{'E[W]':>10} | {'Latence':>10}")
    print(f"{'-'*5}-+-{'-'*15}-+-{'-'*12}-+-{'-'*10}-+-{'-'*10}")
    
    for i, p in enumerate(BACKUP_PROBS):
        print(f"{p:5.2f} | {results_prob['blank_page_rate_mean'][i]*100:14.2f}% | "
              f"{results_prob['storage_cost_mean'][i]:12.1f} | "
              f"{results_prob['sojourn_mean'][i]:10.4f} | "
              f"{results_prob['backup_latency_mean'][i]:10.4f}")
    
    # Graphique probabilité
    plot_probability_analysis(LAMBDA_FIXED, results_prob, 
                              save_path="img/backup_probability_analysis.png")
    
    # =========================================================================
    # 3. CONCLUSIONS
    # =========================================================================
    
    print("\n" + "="*80)
    print("📋 CONCLUSIONS DE L'ANALYSE")
    print("="*80)
    
    print("""
    1. BACKUP SYSTÉMATIQUE vs SANS BACKUP:
       • Élimine quasi-totalement les pages blanches
       • Coût en stockage proportionnel au débit
       • Latence additionnelle = temps moyen de backup
    
    2. BACKUP ALÉATOIRE (p=0.5):
       • Réduit ~50% des pages blanches
       • Économise ~50% du stockage vs systématique
       • Bon compromis coût/fiabilité
    
    3. RECOMMANDATIONS:
       • Charge faible (λ petit): backup aléatoire suffisant
       • Charge élevée (λ grand): backup systématique recommandé
       • Ajuster p selon le coût du stockage vs importance des résultats
    """)
    
    return results_lambda, results_prob


if __name__ == "__main__":
    results_lambda, results_prob = main()
