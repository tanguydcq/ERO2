# 🎓 Simulation de Files d'Attente pour Infrastructure de Correction Automatique

> **ERO2 - Recherche Opérationnelle**  
> Modélisation et simulation à événements discrets d'un système de correction automatique de code

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Modèle 1 : Files infinies (M/M/K → M/M/1)](#modèle-1--files-infinies-mmk--mm1)
4. [Modèle 2 : Capacités finies (M/M/K/ks → M/M/1/kf)](#modèle-2--capacités-finies-mmkks--mm1kf)
5. [Modèle 3 : Mécanisme de backup](#modèle-3--mécanisme-de-backup)
6. [Modèle 4 : Multi-populations (ING vs PREPA)](#modèle-4--multi-populations-ing-vs-prepa)
7. [Modèle 5 : Blocage périodique](#modèle-5--blocage-périodique)
8. [Installation et exécution](#installation-et-exécution)
9. [Résultats et graphiques](#résultats-et-graphiques)

---

## Vue d'ensemble

Ce projet implémente une série de simulateurs à **événements discrets** pour modéliser une infrastructure de correction automatique de code (type moulinette EPITA). Le système est composé de :

- **Station 1** : Exécution des tests (K serveurs parallèles)
- **Station 2** : Envoi des résultats (1 serveur)

Chaque modèle ajoute progressivement des fonctionnalités réalistes :

| Modèle | Fichier | Fonctionnalité principale |
|--------|---------|---------------------------|
| Base | `tandem_queue_simulation.py` | Files infinies, validation théorique |
| Capacités finies | `tandem_queue_finite.py` | Rejets et pertes |
| Backup | `tandem_queue_backup.py` | Sauvegarde des résultats |
| Multi-populations | `tandem_queue_populations.py` | ING vs PREPA différenciés |
| Blocage | `tandem_queue_blocking.py` | Maintenance périodique |

---

## Architecture du système

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    SYSTÈME TANDEM                        │
                    │                                                          │
  Arrivées          │   ┌─────────────────┐       ┌─────────────────┐         │
  (Poisson λ)  ────►│   │   STATION 1     │       │   STATION 2     │         │──► Sortie
                    │   │   K serveurs    │──────►│   1 serveur     │         │
                    │   │   (tests)       │       │   (envoi)       │         │
                    │   └─────────────────┘       └─────────────────┘         │
                    │         μ₁                        μ₂                     │
                    └─────────────────────────────────────────────────────────┘
```

### Notation de Kendall

- **M** : Processus Markovien (exponentiel)
- **M/M/K** : Arrivées Poisson, service exponentiel, K serveurs
- **M/M/K/N** : Idem avec capacité totale N

---

## Modèle 1 : Files infinies (M/M/K → M/M/1)

### 📁 Fichier : `tandem_queue_simulation.py`

### Cadre théorique

Réseau de Jackson en tandem avec deux stations :
- **Station 1** : M/M/K (K serveurs parallèles)
- **Station 2** : M/M/1 (serveur unique)

Par le **théorème de Burke**, la sortie d'une file M/M/K stable est un processus de Poisson de même taux λ.

### Paramètres

| Paramètre | Symbole | Description | Valeur par défaut |
|-----------|---------|-------------|-------------------|
| `lambda_rate` | λ | Taux d'arrivée (jobs/temps) | 4.0 |
| `mu1` | μ₁ | Taux de service station 1 (par serveur) | 2.0 |
| `mu2` | μ₂ | Taux de service station 2 | 5.0 |
| `K` | K | Nombre de serveurs station 1 | 3 |

### Conditions de stabilité

$$\rho_1 = \frac{\lambda}{K \mu_1} < 1 \quad \text{ET} \quad \rho_2 = \frac{\lambda}{\mu_2} < 1$$

### Métriques calculées

- **Temps de séjour moyen** E[W] = E[W₁] + E[W₂]
- **Variance** Var[W]
- **Intervalle de confiance** à 95%
- Comparaison avec valeurs théoriques (formule d'Erlang C)

### Résultats typiques

```
E[W] théorique = 1.7222
E[W] simulé    = 1.7151
Erreur         = 0.41%
```

### Conséquences

- ✅ Le simulateur valide les formules théoriques
- ✅ Base solide pour les extensions
- ⚠️ Hypothèse irréaliste : capacité infinie

---

## Modèle 2 : Capacités finies (M/M/K/ks → M/M/1/kf)

### 📁 Fichier : `tandem_queue_finite.py`

### Cadre

Introduction de **capacités limitées** réalistes :
- **ks** : Capacité totale de la station 1 (file + K serveurs)
- **kf** : Capacité totale de la station 2 (file + 1 serveur)

```
Arrivées → [Station 1: ks places] → [Station 2: kf places] → Sortie
               ↓                          ↓
           REJET                       PERTE
        (push tags)                (résultats)
```

### Paramètres additionnels

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `ks` | Capacité station 1 | 10 |
| `kf` | Capacité station 2 | 5 |

### Nouveaux événements

- **Rejet** : Job arrivant quand station 1 pleine → push tag rejeté
- **Perte** : Job sortant de S1 quand station 2 pleine → résultat perdu

### Métriques additionnelles

| Métrique | Formule |
|----------|---------|
| Taux de rejet | `rejections / arrivals` |
| Taux de perte | `losses / (arrivals - rejections)` |
| Débit effectif | `completions / temps_total` |

### Résultats typiques (ks=10, kf=5)

| λ | Rejet | Perte | E[W] | Débit |
|---|-------|-------|------|-------|
| 4.0 | 0.94% | 8.50% | 1.20 | 3.25 |
| 6.0 | 10.5% | 19.4% | 1.71 | 3.91 |
| 10.0 | 41.0% | 24.3% | 2.21 | 4.05 |

### Conséquences

- 📉 Le **débit sature** (goulot d'étranglement)
- 📈 Le **taux de perte plafonne** (~24% pour kf=5)
- ⚖️ **Trade-off** : augmenter la capacité → moins de pertes mais E[W] plus grand

### Graphiques générés

- `queue_analysis.png` : Évolution des métriques vs λ
- `capacity_comparison.png` : Comparaison de configurations

---

## Modèle 3 : Mécanisme de backup

### 📁 Fichier : `tandem_queue_backup.py`

### Cadre

Ajout d'un **mécanisme de sauvegarde** entre les deux stations pour éviter les "pages blanches" (résultats indisponibles).

```
Arrivées → [Station 1] → [Backup?] → [Station 2] → Sortie
                            ↓
                      [Storage]
                            ↑
                    Réessai si S2 pleine
```

### Modes de backup

| Mode | Description | Probabilité |
|------|-------------|-------------|
| `NONE` | Pas de backup | p = 0 |
| `RANDOM` | Backup aléatoire | 0 < p < 1 |
| `SYSTEMATIC` | Backup systématique | p = 1 |

### Paramètres additionnels

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `backup_mode` | Mode de backup | `NONE` |
| `backup_prob` | Probabilité (mode RANDOM) | 0.5 |
| `backup_time_mean` | Temps moyen de sauvegarde | 0.1 |
| `retry_delay` | Délai avant réessai | 0.5 |
| `max_retries` | Nombre max de réessais | 3 |
| `storage_cost_per_backup` | Coût unitaire | 1.0 |

### Métriques additionnelles

| Métrique | Description |
|----------|-------------|
| **Taux de pages blanches** | Jobs perdus sans backup / jobs traités |
| **Coût en stockage** | Nombre de backups × coût unitaire |
| **Latence induite** | Temps moyen de sauvegarde |

### Résultats typiques (λ = 6.0)

| Stratégie | Pages blanches | Stockage | E[W] | Latence |
|-----------|----------------|----------|------|---------|
| Sans backup | **19.4%** | 0 | 1.70 | 0 |
| Backup p=0.5 | **14.0%** | 4057 | 1.92 | 0.10 |
| Systématique | **0.0%** | 8089 | 2.25 | 0.10 |

### Conséquences

- ✅ **Backup systématique** : élimine les pages blanches
- 💰 **Coût** : proportionnel au débit
- ⏱️ **Latence** : additionnelle constante (~0.1)
- ⚖️ **Backup aléatoire p=0.5** : bon compromis (30% de réduction pour 50% du coût)

### Graphiques générés

- `backup_comparison.png` : Comparaison des stratégies
- `backup_probability_analysis.png` : Trade-off fiabilité vs coût

---

## Modèle 4 : Multi-populations (ING vs PREPA)

### 📁 Fichier : `tandem_queue_populations.py`

### Cadre

Deux populations d'étudiants avec des **caractéristiques de service différentes** :

```
ING    (λ_ing, μ₁_ing, μ₂_ing)   ─┐
                                  ├→ [Station 1: K serveurs] → [Station 2] → Sortie
PREPA  (λ_prepa, μ₁_prepa, μ₂_prepa) ─┘
                                  (File FIFO partagée)
```

### Caractéristiques des populations

| Population | Description | μ₁ | μ₂ | E[Service S1] | E[Service S2] |
|------------|-------------|-----|-----|---------------|---------------|
| **ING** | Code optimisé, tests rapides | 4.0 | 8.0 | 0.25 | 0.125 |
| **PREPA** | Code moins optimisé, tests longs | 1.0 | 3.0 | 1.00 | 0.333 |

### Paramètres

| Paramètre | Description |
|-----------|-------------|
| `lambda_ing` | Taux d'arrivée ING |
| `lambda_prepa` | Taux d'arrivée PREPA |
| `mu1_ing`, `mu2_ing` | Taux de service ING |
| `mu1_prepa`, `mu2_prepa` | Taux de service PREPA |

### Métriques par population

- E[W] par population
- Distribution des temps de séjour
- Percentiles (P50, P90, P99)
- Temps d'attente décomposé (S1 + S2)

### Résultats typiques

| Métrique | ING | PREPA | Ratio P/I |
|----------|-----|-------|-----------|
| **E[W]** | 7.17 | 8.07 | **1.13x** |
| P50 | 7.40 | 8.26 | 1.12x |
| P90 | 11.22 | 12.32 | 1.10x |
| P99 | 14.06 | 15.53 | 1.10x |

### Impact du ratio ING/PREPA

| % ING | E[W] ING | E[W] PREPA |
|-------|----------|------------|
| 10% | 35.8 | 36.6 |
| 50% | 10.3 | 11.2 |
| 90% | **0.86** | **1.81** |

### Conséquences

- 📊 **Surcoût PREPA** : +13% par rapport aux ING
- 🔄 **Interaction** : les PREPA "ralentissent" les ING via les files partagées
- 📈 **Effet de dilution** : plus d'ING → meilleures performances globales
- 💡 **Recommandation** : séparer les files si possible pour l'équité

### Graphiques générés

- `population_comparison.png` : Comparaison globale
- `distributions_detail.png` : Distributions détaillées
- `ratio_study.png` : Impact du ratio ING/PREPA

---

## Modèle 5 : Blocage périodique

### 📁 Fichier : `tandem_queue_blocking.py`

### Cadre

Modélisation de la **maintenance périodique** des serveurs :

```
Cycle : |← tb (fermé) →|← tb/2 (ouvert) →|← tb (fermé) →|...

Disponibilité = tb/2 / (tb + tb/2) = 1/3 ≈ 33.3%
```

Pendant le blocage :
- Les serveurs **ne démarrent pas** de nouveaux services
- Les jobs en cours **terminent** leur service
- Les arrivées **s'accumulent** dans la file

### Paramètres additionnels

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `tb` | Durée de blocage (0 = pas de blocage) | 0.0 |
| `block_s1` | Bloquer station 1 | True |
| `block_s2` | Bloquer station 2 | True |
| `sync_blocking` | Blocage synchronisé | True |

### Métriques d'équité

| Métrique | Description |
|----------|-------------|
| **Ratio P/I** | E[W]_PREPA / E[W]_ING (1 = équitable) |
| **Coefficient de Gini** | 0 = égalité parfaite, 1 = inégalité max |
| **Indice de Jain** | 1 = parfaitement équitable |
| **CV** | Coefficient de variation (σ/μ) |

### Résultats typiques

| tb | Disponibilité | E[W] ING | E[W] PREPA | Ratio P/I | Jain |
|----|---------------|----------|------------|-----------|------|
| **0** (sans) | 100% | 7.23 | 8.13 | 1.124 | 0.839 |
| 5.0 | 33.3% | 58.11 | 59.49 | **1.024** | **0.988** |
| 10.0 | 33.3% | 62.96 | 64.65 | 1.027 | 0.984 |

### Analyse détaillée (tb = 5.0)

| Métrique | Sans blocage | Avec blocage | Variation |
|----------|--------------|--------------|-----------|
| E[W] ING | 7.17 | 58.05 | **+710%** |
| Ratio P/I | 1.127 | **1.024** | -9% |
| Gini | 0.251 | **0.064** | -75% |
| Jain | 0.837 | **0.987** | +18% |
| CV | 0.45 | **0.11** | -76% |

### Conséquences

- ⏱️ **Temps de séjour** : multiplié par ~8x (proportionnel à 1/disponibilité)
- 📉 **CV diminue** : distribution plus homogène
- ⚖️ **Paradoxe de l'équité** : le blocage pénalise tout le monde mais **améliore l'équité** car le temps d'attente dû au blocage "dilue" l'avantage des ING

### Graphiques générés

- `blocking_comparison.png` : Impact de tb sur E[W] et variance
- `fairness_analysis.png` : Analyse détaillée de l'équité

---

## Installation et exécution

### Prérequis

- Python 3.8+
- matplotlib (pour les graphiques)

### Installation

```bash
# Cloner le repository
cd /chemin/vers/ERO2

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
source venv/bin/activate.fish  # Fish shell

# Installer les dépendances
pip install matplotlib
```

### Exécution

```bash
# Modèle 1 : Files infinies
python3 tandem_queue_simulation.py

# Modèle 2 : Capacités finies
python3 tandem_queue_finite.py

# Modèle 3 : Backup
python3 tandem_queue_backup.py

# Modèle 4 : Multi-populations
python3 tandem_queue_populations.py

# Modèle 5 : Blocage périodique
python3 tandem_queue_blocking.py
```

### Personnalisation des paramètres

Chaque script contient une section `# PARAMÈTRES` en début de `main()` :

```python
# Exemple pour tandem_queue_simulation.py
LAMBDA = 4.0      # Taux d'arrivée
MU1 = 2.0         # Taux de service station 1
MU2 = 5.0         # Taux de service station 2
K = 3             # Nombre de serveurs

N_TRAJECTORIES = 30           # Simulations indépendantes
JOBS_PER_TRAJECTORY = 10000   # Jobs par simulation
WARMUP_JOBS = 1000            # Période de chauffe
```

---

## Résultats et graphiques

### Liste des graphiques générés

| Fichier | Description |
|---------|-------------|
| `queue_analysis.png` | Métriques vs λ (capacités finies) |
| `capacity_comparison.png` | Comparaison de configurations |
| `backup_comparison.png` | Stratégies de backup |
| `backup_probability_analysis.png` | Trade-off fiabilité/coût |
| `population_comparison.png` | ING vs PREPA |
| `distributions_detail.png` | Distributions des temps de séjour |
| `ratio_study.png` | Impact du ratio ING/PREPA |
| `blocking_comparison.png` | Impact du blocage |
| `fairness_analysis.png` | Analyse d'équité |

---

## 📚 Références théoriques

- **Théorème de Burke** : Sortie d'une M/M/K stable = Poisson(λ)
- **Réseau de Jackson** : Indépendance des files en régime stationnaire
- **Formule d'Erlang C** : Probabilité d'attente en M/M/K
- **Indice de Jain** : Mesure d'équité (J = (Σxᵢ)² / (n·Σxᵢ²))
- **Coefficient de Gini** : Mesure d'inégalité

---

## 🎓 Auteur

Projet ERO2 - Recherche Opérationnelle  
EPITA - Janvier 2026