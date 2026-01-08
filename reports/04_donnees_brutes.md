# Résultats Bruts et Données de Simulation

> **Projet ERO2 - Recherche Opérationnelle**  
> Données Consolidées pour Vérification  
> Date : Janvier 2026

---

## Table des Matières

1. [Méthodologie de Simulation](#1-méthodologie-de-simulation)
2. [Modèle 1 : Files Infinies](#2-modèle-1-files-infinies)
3. [Modèle 2 : Capacités Finies](#3-modèle-2-capacités-finies)
4. [Modèle 3 : Backup](#4-modèle-3-backup)
5. [Modèle 4 : Multi-Populations](#5-modèle-4-multi-populations)
6. [Modèle 5 : Blocage Périodique](#6-modèle-5-blocage-périodique)
7. [Modèle Alternatif : Priorités](#7-modèle-alternatif-priorités)
8. [Analyse de Stabilité](#8-analyse-de-stabilité)

---

## 1. Méthodologie de Simulation

### 1.1 Paramètres Communs (Mise à jour 08/01/2026)

> **Recommandations Coach** : 1000 trajectoires pour des intervalles de confiance robustes

```
Graine aléatoire (seed)      : 42
Nombre de trajectoires       : 1000
Jobs par trajectoire         : 5,000
Période de chauffe (warmup)  : 500 jobs
Intervalle de confiance      : 95% (Student t)
```

### 1.2 Validation Statistique

- **Convergence** : Vérifiée par analyse de la variance inter-trajectoires
- **Stationnarité** : Warmup de 500 jobs pour atteindre le régime permanent
- **Indépendance** : Réinitialisation complète entre trajectoires
- **Principe de superposition** : Validé pour les populations ING + PREPA

### 1.3 Justification du Nombre de Trajectoires

Avec $n = 1000$ trajectoires, la demi-largeur de l'IC 95% est :

$$\text{Demi-largeur} = t_{0.975, 999} \times \frac{s}{\sqrt{n}} \approx 1.96 \times \frac{s}{31.6}$$

Cela garantit une précision d'environ $\pm 0.01$ pour les estimateurs de moyenne.

---

## 2. Modèle 1 : Files Infinies (M/M/K → M/M/1)

### 2.1 Paramètres

```
λ  = 4.0 jobs/min    (Taux d'arrivée)
μ₁ = 2.0 jobs/min    (Taux service S1, par serveur)
μ₂ = 5.0 jobs/min    (Taux service S2)
K  = 3               (Nombre de serveurs S1)
Trajectoires = 1000
Jobs/trajectoire = 5,000
Warmup = 500
```

### 2.2 Statistiques Agrégées (Résultats Réels - 1000 trajectoires)

```
E[W] moyen             : 1.7195
Variance (empirique)   : 1.3862
Écart-type             : 1.1773
Erreur standard        : 0.0046
IC 95%                 : [1.7105, 1.7285]
Demi-largeur IC        : ±0.0090

Total jobs analysés    : 4,500,000
```

### 2.3 Comparaison Théorique

| Métrique | Théorique | Simulé | Erreur (%) |
|----------|-----------|--------|------------|
| ρ₁ | 0.6667 | 0.6667 | 0.00% |
| ρ₂ | 0.8000 | 0.8000 | 0.00% |
| E[W₁] | 0.7222 | 0.720 ± 0.003 | 0.28% |
| E[W₂] | 1.0000 | 1.000 ± 0.002 | 0.00% |
| **E[W]** | **1.7222** | **1.7195 ± 0.0090** | **0.16%** |

**Conclusion** : Excellente concordance simulation/théorie (erreur < 0.2% avec 1000 trajectoires).

---

## 3. Modèle 2 : Capacités Finies (M/M/K/ks → M/M/1/kf)

### 3.1 Paramètres

```
μ₁ = 2.0    μ₂ = 5.0    K = 3
Trajectoires : 1000
Jobs/traj : 5,000
Warmup : 500
```

### 3.2 Étude Paramétrique - Configuration (ks=10, kf=5) - 1000 trajectoires

| λ | Rejet (%) | Perte (%) | E[W] | IC 95% |
|---|-----------|-----------|------|--------|
| 4.0 | 0.89 | 8.50 | 1.1969 | ±0.0019 |
| 6.0 | 10.11 | 19.47 | 1.7016 | ±0.0028 |

### 3.3 Comparaison des Configurations de Capacité (Résultats Réels)

**Configuration (ks=5, kf=3) - Petite**
| λ | Rejet (%) | Perte (%) | E[W] | Débit |
|---|-----------|-----------|------|-------|
| 1.0 | 0.02 | 0.54 | 0.748 | 0.895 |
| 4.0 | 7.48 | 13.87 | 0.944 | 2.864 |
| 6.0 | 20.19 | 22.26 | 1.050 | 3.368 |
| 8.0 | 33.57 | 25.94 | 1.133 | 3.543 |

**Configuration (ks=10, kf=5) - Moyenne**
| λ | Rejet (%) | Perte (%) | E[W] | Débit |
|---|-----------|-----------|------|-------|
| 1.0 | 0.00 | 0.04 | 0.752 | 0.905 |
| 4.0 | 1.07 | 8.56 | 1.206 | 3.259 |
| 6.0 | 10.12 | 19.55 | 1.704 | 3.911 |
| 8.0 | 27.01 | 24.09 | 2.063 | 4.011 |

**Configuration (ks=20, kf=10) - Grande**
| λ | Rejet (%) | Perte (%) | E[W] | Débit |
|---|-----------|-----------|------|-------|
| 1.0 | 0.00 | 0.00 | 0.753 | 0.904 |
| 4.0 | 0.01 | 1.85 | 1.437 | 3.530 |
| 6.0 | 4.89 | 15.32 | 3.135 | 4.345 |
| 8.0 | 25.36 | 19.72 | 4.378 | 4.332 |

**Configuration (ks=50, kf=20) - Très grande**
| λ | Rejet (%) | Perte (%) | E[W] | Débit |
|---|-----------|-----------|------|-------|
| 1.0 | 0.00 | 0.00 | 0.749 | 0.897 |
| 4.0 | 0.00 | 0.21 | 1.652 | 3.581 |
| 6.0 | 1.85 | 16.10 | 7.299 | 4.453 |
| 8.0 | 25.36 | 16.59 | 11.028 | 4.486 |

### 3.4 Exemple Détaillé (λ=6.0, ks=10, kf=5)

```
Arrivées totales     : 9,000
Jobs rejetés         : 949 (10.54%)
Jobs perdus          : 1,691 (21.00%)
Jobs complétés       : 6,354
Temps de séjour moyen: 1.7473
Variance temps séjour: 0.6307
Débit effectif       : 3.8260
```

---

## 4. Modèle 3 : Backup

### 4.1 Paramètres

```
λ = 6.0 (charge élevée)
μ₁ = 2.0    μ₂ = 5.0    K = 3
ks = 10     kf = 5
backup_time = 0.1
Trajectoires : 200
```

### 4.2 Comparaison des Stratégies de Backup (Résultats 200 trajectoires)

| p_backup | Pages Blanches (%) | E[W] | IC 95% |
|----------|-------------------|------|--------|
| 0.00 (Aucun) | 19.54 | 1.7004 | ±0.0083 |
| 0.25 | 17.59 | 1.8047 | ±0.0087 |
| 0.50 | 14.32 | 1.9317 | ±0.0087 |
| 0.75 | 8.85 | 2.0755 | ±0.0096 |
| 1.00 (Systématique) | 0.00 | 2.2390 | ±0.0103 |

### 4.3 Analyse de l'Impact de la Probabilité de Backup (λ=6.0)

| p | Pages Blanches (%) | Stockage | E[W] | Latence |
|---|-------------------|----------|------|---------|
| 0.00 | 19.42 | 0.0 | 1.699 | 0.0000 |
| 0.10 | 18.36 | 803.3 | 1.739 | 0.1001 |
| 0.25 | 17.48 | 2,011.3 | 1.801 | 0.1001 |
| 0.50 | 14.04 | 4,056.8 | 1.922 | 0.0996 |
| 0.75 | 8.91 | 6,074.3 | 2.066 | 0.0997 |
| 0.90 | 4.04 | 7,275.1 | 2.166 | 0.1002 |
| 1.00 | 0.00 | 8,088.6 | 2.252 | 0.0998 |

### 4.4 Statistiques Agrégées

```
Réduction moyenne pages blanches (systématique) : 100.0%
Coût moyen stockage - Systématique              : 8,226.1
Coût moyen stockage - Aléatoire p=0.5           : 4,110.0
Économie avec backup aléatoire                  : 50.0%
Latence moyenne induite (systématique)          : 0.1000
```

---

## 5. Modèle 4 : Multi-Populations (ING vs PREPA)

### 5.1 Paramètres

```
ING   : λ=3.0, μ1=2.5, μ2=5.0 (service court)
PREPA : λ=1.5, μ1=1.5, μ2=4.0 (service long)
λ_total = λ_ING + λ_PREPA = 4.5 (Principe de superposition)
K = 3 serveurs
Trajectoires = 1000
```

### 5.2 Résultats Comparatifs (Résultats Réels - 1000 trajectoires)

| Métrique | ING | PREPA | Ratio P/I |
|----------|-----|-------|-----------|
| Temps de séjour moyen | 2.8363 | 3.1124 | 1.10x |
| IC 95% | ±0.0030 | ±0.0045 | - |
| Attente moyenne S1 | 0.243 | 0.245 | 1.01x |
| Attente moyenne S2 | 6.5465 | 6.4867 | 0.99x |
| Percentile 50% | 7.4049 | 8.2580 | 1.12x |
| Percentile 90% | 11.2221 | 12.3224 | 1.10x |
| Percentile 99% | 14.0550 | 15.5276 | 1.10x |

### 5.3 Résumé

```
• Les PREPA ont un temps de séjour 10% plus long que les ING
• Différence absolue : 0.276 unités de temps
• Principe de superposition validé : λ_total = 4.5 = 3.0 + 1.5
```

### 5.4 Étude de l'Impact du Ratio ING/PREPA (λ total = 5.0)

| Ratio ING | E[W] ING | E[W] PREPA | Ratio P/I |
|-----------|----------|------------|-----------|
| 10% | 35.811 | 36.613 | 1.02 |
| 20% | 31.271 | 32.080 | 1.03 |
| 30% | 18.195 | 19.143 | 1.05 |
| 40% | 12.895 | 13.818 | 1.07 |
| 50% | 10.317 | 11.217 | 1.09 |
| 60% | 7.244 | 8.143 | 1.12 |
| 70% | 3.248 | 4.150 | 1.28 |
| 80% | 1.473 | 2.397 | 1.63 |
| 90% | 0.861 | 1.812 | 2.10 |

---

## 6. Modèle 5 : Blocage Périodique

### 6.1 Paramètres

```
ING   : λ=3.0, μ1=2.5, μ2=5.0
PREPA : λ=1.5, μ1=1.5, μ2=4.0
K = 3 serveurs
Cycle : tb (fermé) → tb/2 (ouvert)
Trajectoires = 100
```

### 6.2 Impact du Temps de Blocage (Résultats Réels - 100 trajectoires)

| tb | E[W] ING | IC 95% | E[W] PREPA | IC 95% | Ratio |
|----|----------|--------|------------|--------|-------|
| 0 | 2.8605 | ±0.0314 | 3.1411 | ±0.0334 | 1.10 |
| 2.0 | 25.6311 | ±0.0509 | 25.9549 | ±0.0503 | 1.01 |
| 5.0 | 30.2730 | ±0.0791 | 30.7105 | ±0.0838 | 1.01 |
| 10.0 | 31.8428 | ±0.1049 | 32.3934 | ±0.1083 | 1.02 |

### 6.3 Analyse d'Équité Détaillée (tb = 5.0)

**Sans blocage:**
```
ING   : E[W]=7.169, Var=10.458, CV=0.451
PREPA : E[W]=8.079, Var=11.463, CV=0.419
Ratio P/I : 1.127
Gini : 0.2513, Jain : 0.8370
```

**Avec blocage (tb=5.0):**
```
ING   : E[W]=58.050, Var=42.298, CV=0.112
PREPA : E[W]=59.450, Var=44.692, CV=0.112
Ratio P/I : 1.024
Gini : 0.0635, Jain : 0.9874
```

### 6.4 Impact du Blocage

```
• Avec tb max = 10.0:
  - Augmentation E[W] ING   : +770.9%
  - Augmentation E[W] PREPA : +695.3%
• Le blocage AMÉLIORE l'équité (ratio plus proche de 1)
  - Sans blocage : ratio = 1.124
  - Avec blocage : ratio = 1.027
```

---

## 7. Modèle Alternatif : Politiques de Priorité

### 7.1 Paramètres

```
λ_ING = 3.0      λ_PREPA = 1.0
μ1_ING = 4.0     μ1_PREPA = 1.0
μ2_ING = 8.0     μ2_PREPA = 3.0
K = 3
Trajectoires : 15
```

### 7.2 Comparaison des Politiques (Résultats Réels)

| Politique | E[W] ING | IC 95% | E[W] PREPA | IC 95% | E[W] Global | Ratio P/I |
|-----------|----------|--------|------------|--------|-------------|-----------|
| **FCFS** | 1.1671 | ±0.0722 | 2.0691 | ±0.0882 | 1.3933 | 1.7728 |
| **SRPT** | 0.7339 | ±0.0193 | 2.4281 | ±0.1044 | 1.1545 | 3.3084 |
| **SEPARATE** | 1.3913 | ±0.1014 | 1.8533 | ±0.0490 | 1.5068 | 1.3321 |
| **PREPA_FIRST** | 1.5392 | ±0.1491 | 1.6603 | ±0.0407 | 1.5692 | 1.0787 |

### 7.3 Analyse des Politiques

| Critère | Meilleure Politique | Valeur |
|---------|---------------------|--------|
| Temps global minimum | SRPT | E[W] = 1.1545 |
| Meilleure équité | PREPA_FIRST | Ratio = 1.0787 |
| Compromis temps/équité | SEPARATE | E[W] = 1.5068, Ratio = 1.3321 |

### 7.4 Recommandations

- **Si objectif = minimiser temps global** : SRPT (mais pénalise fortement PREPA)
- **Si objectif = équité stricte** : PREPA_FIRST (ratio proche de 1)
- **Si objectif = compromis** : SEPARATE (files séparées avec alternance)

---

## 8. Analyse de Stabilité

### 8.1 Paramètres

```
μ₁ = 2.0    μ₂ = 5.0    K = 3
```

### 8.2 Carte de Stabilité

| λ | ρ₁ | ρ₂ | Stable | Goulot |
|---|-----|-----|--------|--------|
| 1.0 | 0.167 | 0.200 | ✓ | - |
| 2.0 | 0.333 | 0.400 | ✓ | S2 |
| 3.0 | 0.500 | 0.600 | ✓ | S2 |
| 4.0 | 0.667 | 0.800 | ✓ | S2 |
| 4.5 | 0.750 | 0.900 | ✓ | S2 |
| 4.8 | 0.800 | 0.960 | ✓ | S2 |
| 5.0 | 0.833 | 1.000 | ✗ | S2 |
| 6.0 | 1.000 | 1.200 | ✗ | Both |

### 8.3 Valeurs Critiques

```
Station 1 (M/M/K avec K=3, μ₁=2.0):
  Capacité maximale    : K × μ₁ = 6.0 jobs/min
  λ critique S1        : 6.0 jobs/min

Station 2 (M/M/1 avec μ₂=5.0):
  Capacité maximale    : μ₂ = 5.0 jobs/min
  λ critique S2        : 5.0 jobs/min

Système global :
  λ critique          : min(6.0, 5.0) = 5.0 jobs/min
  Goulot              : Station 2
  Recommandation      : λ < 4.0 pour marge ≥ 20%
```

---

## Annexe : Graphiques Générés

Les graphiques suivants ont été générés dans le dossier `img/` :

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
| `policy_comparison.png` | Comparaison des politiques de priorité |

---

*Données générées avec seed=42 pour reproductibilité - Janvier 2026*
