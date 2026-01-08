#!/usr/bin/env python3
"""
Simulation à événements discrets d'un réseau de files d'attente en tandem.

Architecture du système :
    Arrivées (Poisson λ) → [Station 1: M/M/K] → [Station 2: M/M/1] → Sortie

Station 1 : K serveurs parallèles, service exponentiel de taux μ1
Station 2 : 1 serveur, service exponentiel de taux μ2

Auteur : Simulation ERO2
Date : Janvier 2026
"""

import random
import heapq
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum, auto


# =============================================================================
# CONSTANTES ET TYPES D'ÉVÉNEMENTS
# =============================================================================

class EventType(Enum):
    """Types d'événements possibles dans la simulation."""
    ARRIVAL = auto()           # Arrivée d'un nouveau job dans le système
    DEPARTURE_STATION1 = auto() # Fin de service à la station 1
    DEPARTURE_STATION2 = auto() # Fin de service à la station 2 (sortie)


@dataclass
class Job:
    """
    Représente un job (travail de correction) dans le système.
    
    Attributes:
        job_id: Identifiant unique du job
        arrival_time: Instant d'arrivée dans le système
        start_service_s1: Instant de début de service à la station 1
        end_service_s1: Instant de fin de service à la station 1
        start_service_s2: Instant de début de service à la station 2
        departure_time: Instant de sortie du système
    """
    job_id: int
    arrival_time: float
    start_service_s1: Optional[float] = None
    end_service_s1: Optional[float] = None
    start_service_s2: Optional[float] = None
    departure_time: Optional[float] = None
    
    def sojourn_time(self) -> float:
        """Calcule le temps de séjour total dans le système."""
        if self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return float('inf')
    
    def waiting_time_s1(self) -> float:
        """Temps d'attente dans la file de la station 1."""
        if self.start_service_s1 is not None:
            return self.start_service_s1 - self.arrival_time
        return float('inf')
    
    def waiting_time_s2(self) -> float:
        """Temps d'attente dans la file de la station 2."""
        if self.start_service_s2 is not None and self.end_service_s1 is not None:
            return self.start_service_s2 - self.end_service_s1
        return float('inf')


@dataclass(order=True)
class Event:
    """
    Représente un événement dans la simulation.
    
    Attributes:
        time: Instant de l'événement
        event_type: Type de l'événement
        job: Job concerné par l'événement
    """
    time: float
    event_type: EventType = field(compare=False)
    job: Job = field(compare=False)


# =============================================================================
# CLASSE PRINCIPALE DU SIMULATEUR
# =============================================================================

class TandemQueueSimulator:
    """
    Simulateur à événements discrets pour un réseau M/M/K -> M/M/1.
    
    Attributes:
        lambda_rate: Taux d'arrivée (processus de Poisson)
        mu1: Taux de service de chaque serveur à la station 1
        mu2: Taux de service du serveur à la station 2
        K: Nombre de serveurs à la station 1
    """
    
    def __init__(self, lambda_rate: float, mu1: float, mu2: float, K: int):
        """
        Initialise le simulateur.
        
        Args:
            lambda_rate: Taux d'arrivée λ
            mu1: Taux de service μ1 (station 1, par serveur)
            mu2: Taux de service μ2 (station 2)
            K: Nombre de serveurs à la station 1
        """
        self.lambda_rate = lambda_rate
        self.mu1 = mu1
        self.mu2 = mu2
        self.K = K
        
        # Vérification des conditions de stabilité
        self.rho1 = lambda_rate / (K * mu1)
        self.rho2 = lambda_rate / mu2
        
        if self.rho1 >= 1:
            print(f"⚠️  ATTENTION: Station 1 instable (ρ1 = {self.rho1:.3f} >= 1)")
        if self.rho2 >= 1:
            print(f"⚠️  ATTENTION: Station 2 instable (ρ2 = {self.rho2:.3f} >= 1)")
        
        self._reset()
    
    def _reset(self):
        """Réinitialise l'état du simulateur."""
        # Horloge de simulation
        self.current_time = 0.0
        
        # Échéancier (tas min pour efficacité)
        self.event_queue: List[Event] = []
        
        # État de la station 1
        self.queue_s1: List[Job] = []      # File d'attente
        self.servers_s1: List[Optional[Job]] = [None] * self.K  # Serveurs
        
        # État de la station 2
        self.queue_s2: List[Job] = []      # File d'attente
        self.server_s2: Optional[Job] = None  # Serveur unique
        
        # Compteurs et statistiques
        self.job_counter = 0
        self.completed_jobs: List[Job] = []
    
    def _schedule_event(self, event: Event):
        """Ajoute un événement à l'échéancier."""
        heapq.heappush(self.event_queue, event)
    
    def _generate_interarrival(self) -> float:
        """Génère un temps inter-arrivée (exponentiel de paramètre λ)."""
        return random.expovariate(self.lambda_rate)
    
    def _generate_service_s1(self) -> float:
        """Génère un temps de service à la station 1 (exponentiel de paramètre μ1)."""
        return random.expovariate(self.mu1)
    
    def _generate_service_s2(self) -> float:
        """Génère un temps de service à la station 2 (exponentiel de paramètre μ2)."""
        return random.expovariate(self.mu2)
    
    def _find_free_server_s1(self) -> int:
        """
        Trouve un serveur libre à la station 1.
        
        Returns:
            Index du serveur libre, ou -1 si tous occupés
        """
        for i, server in enumerate(self.servers_s1):
            if server is None:
                return i
        return -1
    
    def _handle_arrival(self, job: Job):
        """
        Traite l'arrivée d'un nouveau job dans le système.
        
        Le job est placé en service à la station 1 s'il y a un serveur libre,
        sinon il est mis en file d'attente.
        """
        # Programmer la prochaine arrivée
        self.job_counter += 1
        next_job = Job(job_id=self.job_counter, arrival_time=self.current_time + self._generate_interarrival())
        self._schedule_event(Event(
            time=next_job.arrival_time,
            event_type=EventType.ARRIVAL,
            job=next_job
        ))
        
        # Chercher un serveur libre à la station 1
        free_server = self._find_free_server_s1()
        
        if free_server >= 0:
            # Serveur disponible : démarrer le service immédiatement
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
            # Tous les serveurs occupés : mise en file d'attente
            self.queue_s1.append(job)
    
    def _handle_departure_s1(self, job: Job):
        """
        Traite la fin de service à la station 1.
        
        Le job passe à la station 2. Si la file 1 n'est pas vide,
        le prochain job en attente commence son service.
        """
        # Libérer le serveur
        for i, server_job in enumerate(self.servers_s1):
            if server_job is not None and server_job.job_id == job.job_id:
                self.servers_s1[i] = None
                break
        
        # S'il y a des jobs en attente à la station 1, en prendre un
        if self.queue_s1:
            next_job = self.queue_s1.pop(0)  # FIFO
            next_job.start_service_s1 = self.current_time
            service_time = self._generate_service_s1()
            next_job.end_service_s1 = self.current_time + service_time
            
            # Trouver un serveur libre (il y en a forcément un)
            free_server = self._find_free_server_s1()
            self.servers_s1[free_server] = next_job
            
            self._schedule_event(Event(
                time=next_job.end_service_s1,
                event_type=EventType.DEPARTURE_STATION1,
                job=next_job
            ))
        
        # Le job actuel passe à la station 2
        if self.server_s2 is None:
            # Serveur 2 libre : service immédiat
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
            # Serveur 2 occupé : mise en file d'attente
            self.queue_s2.append(job)
    
    def _handle_departure_s2(self, job: Job):
        """
        Traite la fin de service à la station 2 (sortie du système).
        
        Le job quitte le système. Si la file 2 n'est pas vide,
        le prochain job commence son service.
        """
        # Libérer le serveur
        self.server_s2 = None
        
        # Enregistrer le job complété
        self.completed_jobs.append(job)
        
        # S'il y a des jobs en attente à la station 2
        if self.queue_s2:
            next_job = self.queue_s2.pop(0)  # FIFO
            next_job.start_service_s2 = self.current_time
            service_time = self._generate_service_s2()
            next_job.departure_time = self.current_time + service_time
            
            self.server_s2 = next_job
            
            self._schedule_event(Event(
                time=next_job.departure_time,
                event_type=EventType.DEPARTURE_STATION2,
                job=next_job
            ))
    
    def run(self, max_jobs: int = 10000, warmup_jobs: int = 1000) -> List[Job]:
        """
        Exécute la simulation.
        
        Args:
            max_jobs: Nombre total de jobs à simuler
            warmup_jobs: Nombre de jobs à ignorer (période de chauffe)
        
        Returns:
            Liste des jobs complétés après la période de chauffe
        """
        self._reset()
        
        # Programmer la première arrivée
        first_job = Job(job_id=0, arrival_time=self._generate_interarrival())
        self._schedule_event(Event(
            time=first_job.arrival_time,
            event_type=EventType.ARRIVAL,
            job=first_job
        ))
        
        # Boucle principale de simulation
        while self.job_counter < max_jobs and self.event_queue:
            # Extraire l'événement le plus proche
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            # Dispatcher selon le type d'événement
            if event.event_type == EventType.ARRIVAL:
                self._handle_arrival(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION1:
                self._handle_departure_s1(event.job)
            elif event.event_type == EventType.DEPARTURE_STATION2:
                self._handle_departure_s2(event.job)
        
        # Retourner les jobs après la période de chauffe
        return [job for job in self.completed_jobs if job.job_id >= warmup_jobs]


# =============================================================================
# FONCTIONS D'ANALYSE STATISTIQUE
# =============================================================================

def compute_statistics(values: List[float]) -> Tuple[float, float, float, float]:
    """
    Calcule les statistiques descriptives d'une liste de valeurs.
    
    Args:
        values: Liste de valeurs numériques
    
    Returns:
        Tuple (moyenne, variance, écart-type, erreur standard)
    """
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    
    # Moyenne
    mean = sum(values) / n
    
    # Variance (estimateur non biaisé)
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    else:
        variance = 0.0
    
    # Écart-type
    std_dev = math.sqrt(variance)
    
    # Erreur standard de la moyenne
    std_error = std_dev / math.sqrt(n) if n > 0 else 0.0
    
    return mean, variance, std_dev, std_error


def run_multiple_simulations(
    lambda_rate: float,
    mu1: float,
    mu2: float,
    K: int,
    n_trajectories: int = 1000,
    jobs_per_trajectory: int = 5000,
    warmup_jobs: int = 500,
    seed: Optional[int] = None
) -> dict:
    """
    Exécute N trajectoires indépendantes et calcule les statistiques globales.
    
    Args:
        lambda_rate: Taux d'arrivée λ
        mu1: Taux de service μ1 (station 1)
        mu2: Taux de service μ2 (station 2)
        K: Nombre de serveurs à la station 1
        n_trajectories: Nombre de simulations indépendantes (1000 recommandé)
        jobs_per_trajectory: Nombre de jobs par simulation
        warmup_jobs: Période de chauffe (jobs ignorés)
        seed: Graine aléatoire (pour reproductibilité)
    
    Returns:
        Dictionnaire contenant toutes les statistiques
    """
    if seed is not None:
        random.seed(seed)
    
    # Stockage des moyennes par trajectoire
    trajectory_means = []
    trajectory_variances = []
    all_sojourn_times = []
    
    print(f"\n{'='*60}")
    print(f"SIMULATION DE {n_trajectories} TRAJECTOIRES INDÉPENDANTES")
    print(f"{'='*60}")
    print(f"Paramètres: λ={lambda_rate}, μ1={mu1}, μ2={mu2}, K={K}")
    print(f"Jobs/trajectoire: {jobs_per_trajectory}, Warmup: {warmup_jobs}")
    print(f"{'='*60}\n")
    
    for i in range(n_trajectories):
        # Créer un nouveau simulateur pour chaque trajectoire
        simulator = TandemQueueSimulator(lambda_rate, mu1, mu2, K)
        completed_jobs = simulator.run(max_jobs=jobs_per_trajectory, warmup_jobs=warmup_jobs)
        
        # Extraire les temps de séjour
        sojourn_times = [job.sojourn_time() for job in completed_jobs]
        
        if sojourn_times:
            mean, var, _, _ = compute_statistics(sojourn_times)
            trajectory_means.append(mean)
            trajectory_variances.append(var)
            all_sojourn_times.extend(sojourn_times)
        
        # Affichage progression
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  Trajectoire {i+1:3d}/{n_trajectories}: "
                  f"E[W] = {mean:.4f}, Var[W] = {var:.4f}")
    
    # Statistiques globales sur les moyennes des trajectoires
    global_mean, var_of_means, std_of_means, std_error = compute_statistics(trajectory_means)
    
    # Statistiques sur l'ensemble des temps de séjour
    overall_mean, overall_var, overall_std, _ = compute_statistics(all_sojourn_times)
    
    # Intervalle de confiance à 95% (approximation normale)
    z_95 = 1.96
    ci_lower = global_mean - z_95 * std_error
    ci_upper = global_mean + z_95 * std_error
    
    results = {
        'parameters': {
            'lambda': lambda_rate,
            'mu1': mu1,
            'mu2': mu2,
            'K': K,
            'rho1': lambda_rate / (K * mu1),
            'rho2': lambda_rate / mu2,
        },
        'simulation': {
            'n_trajectories': n_trajectories,
            'jobs_per_trajectory': jobs_per_trajectory,
            'warmup_jobs': warmup_jobs,
            'total_jobs_analyzed': len(all_sojourn_times),
        },
        'sojourn_time': {
            'mean': global_mean,
            'variance': overall_var,
            'std_dev': overall_std,
            'std_error': std_error,
            'ci_95_lower': ci_lower,
            'ci_95_upper': ci_upper,
        },
        'trajectory_stats': {
            'means': trajectory_means,
            'variances': trajectory_variances,
        }
    }
    
    return results


def theoretical_values(lambda_rate: float, mu1: float, mu2: float, K: int) -> dict:
    """
    Calcule les valeurs théoriques pour comparaison.
    
    Args:
        lambda_rate: Taux d'arrivée
        mu1: Taux de service station 1
        mu2: Taux de service station 2
        K: Nombre de serveurs station 1
    
    Returns:
        Dictionnaire avec les valeurs théoriques
    """
    rho1 = lambda_rate / (K * mu1)
    rho2 = lambda_rate / mu2
    
    if rho1 >= 1 or rho2 >= 1:
        return {'error': 'Système instable - pas de valeurs théoriques'}
    
    # Station 2 (M/M/1) - formules exactes
    W2 = 1 / (mu2 - lambda_rate)  # Temps moyen dans station 2
    
    # Station 1 (M/M/K) - approximations
    # Probabilité d'attente (formule d'Erlang C simplifiée pour K petit)
    a = lambda_rate / mu1  # Intensité de trafic totale
    
    # Calcul de P0 (probabilité système vide)
    sum_terms = sum((a ** n) / math.factorial(n) for n in range(K))
    last_term = (a ** K) / (math.factorial(K) * (1 - rho1))
    P0 = 1 / (sum_terms + last_term)
    
    # Probabilité d'attente (Erlang C)
    PQ = ((a ** K) / (math.factorial(K) * (1 - rho1))) * P0
    
    # Temps moyen d'attente dans la file
    Wq1 = PQ / (K * mu1 - lambda_rate)
    
    # Temps moyen dans la station 1
    W1 = Wq1 + 1 / mu1
    
    # Temps total théorique
    W_total = W1 + W2
    
    return {
        'rho1': rho1,
        'rho2': rho2,
        'W1': W1,
        'W2': W2,
        'W_total': W_total,
        'Wq1': Wq1,
        'P_wait': PQ,
    }


def print_results(results: dict, theoretical: dict = None):
    """
    Affiche les résultats de manière formatée.
    
    Args:
        results: Résultats de la simulation
        theoretical: Valeurs théoriques (optionnel)
    """
    print(f"\n{'='*60}")
    print("RÉSULTATS DE LA SIMULATION")
    print(f"{'='*60}")
    
    params = results['parameters']
    print(f"\n📊 PARAMÈTRES DU SYSTÈME:")
    print(f"   λ (taux d'arrivée)     = {params['lambda']:.4f}")
    print(f"   μ1 (service station 1) = {params['mu1']:.4f}")
    print(f"   μ2 (service station 2) = {params['mu2']:.4f}")
    print(f"   K (serveurs station 1) = {params['K']}")
    print(f"   ρ1 = λ/(Kμ1)          = {params['rho1']:.4f}")
    print(f"   ρ2 = λ/μ2             = {params['rho2']:.4f}")
    
    sim = results['simulation']
    print(f"\n📈 CONFIGURATION SIMULATION:")
    print(f"   Trajectoires           = {sim['n_trajectories']}")
    print(f"   Jobs par trajectoire   = {sim['jobs_per_trajectory']}")
    print(f"   Période de chauffe     = {sim['warmup_jobs']}")
    print(f"   Jobs analysés (total)  = {sim['total_jobs_analyzed']}")
    
    soj = results['sojourn_time']
    print(f"\n⏱️  TEMPS DE SÉJOUR TOTAL:")
    print(f"   Moyenne (empirique)    = {soj['mean']:.4f}")
    print(f"   Variance (empirique)   = {soj['variance']:.4f}")
    print(f"   Écart-type            = {soj['std_dev']:.4f}")
    print(f"   Erreur standard       = {soj['std_error']:.4f}")
    print(f"   IC 95%                = [{soj['ci_95_lower']:.4f}, {soj['ci_95_upper']:.4f}]")
    
    if theoretical and 'error' not in theoretical:
        print(f"\n📐 COMPARAISON AVEC VALEURS THÉORIQUES:")
        print(f"   E[W] théorique        = {theoretical['W_total']:.4f}")
        print(f"   E[W] simulé           = {soj['mean']:.4f}")
        error_pct = abs(theoretical['W_total'] - soj['mean']) / theoretical['W_total'] * 100
        print(f"   Erreur relative       = {error_pct:.2f}%")
        print(f"   W1 théorique          = {theoretical['W1']:.4f}")
        print(f"   W2 théorique          = {theoretical['W2']:.4f}")
    
    print(f"\n{'='*60}\n")


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal du programme."""
    
    # =========================================================================
    # PARAMÈTRES DE SIMULATION (À MODIFIER SELON VOS BESOINS)
    # =========================================================================
    
    # Paramètres du système de files d'attente
    LAMBDA = 4.0      # Taux d'arrivée (jobs/unité de temps)
    MU1 = 2.0         # Taux de service station 1 (par serveur)
    MU2 = 5.0         # Taux de service station 2
    K = 3             # Nombre de serveurs à la station 1
    
    # Paramètres de simulation (1000 trajectoires - recommandation coach 16/12/2025)
    N_TRAJECTORIES = 1000         # Nombre de simulations indépendantes (augmenté pour IC robustes)
    JOBS_PER_TRAJECTORY = 5000    # Jobs simulés par trajectoire
    WARMUP_JOBS = 500             # Jobs ignorés (régime transitoire)
    SEED = 42                      # Graine aléatoire (None pour aléatoire)
    
    # =========================================================================
    # EXÉCUTION
    # =========================================================================
    
    print("\n" + "🚀 " * 20)
    print("   SIMULATEUR DE FILES D'ATTENTE EN TANDEM (M/M/K → M/M/1)")
    print("🚀 " * 20)
    
    # Calcul des valeurs théoriques
    theoretical = theoretical_values(LAMBDA, MU1, MU2, K)
    
    # Exécution des simulations
    results = run_multiple_simulations(
        lambda_rate=LAMBDA,
        mu1=MU1,
        mu2=MU2,
        K=K,
        n_trajectories=N_TRAJECTORIES,
        jobs_per_trajectory=JOBS_PER_TRAJECTORY,
        warmup_jobs=WARMUP_JOBS,
        seed=SEED
    )
    
    # Affichage des résultats
    print_results(results, theoretical)
    
    # =========================================================================
    # EXEMPLE D'UTILISATION PROGRAMMATIQUE
    # =========================================================================
    
    print("💡 EXEMPLE D'ACCÈS AUX RÉSULTATS:")
    print(f"   results['sojourn_time']['mean']     = {results['sojourn_time']['mean']:.4f}")
    print(f"   results['sojourn_time']['variance'] = {results['sojourn_time']['variance']:.4f}")
    print(f"   Nombre de trajectoires: {len(results['trajectory_stats']['means'])}")
    
    return results


if __name__ == "__main__":
    results = main()
