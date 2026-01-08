# 🎓 ERO2 - Simulation de Files d'Attente

> Simulation à événements discrets d'une infrastructure de correction automatique de code (moulinette)
> **1000 trajectoires** pour des intervalles de confiance robustes

---

## 📋 Vue d'ensemble

Ce projet modélise un système de correction automatique en **réseau de files tandem** (M/M/K → M/M/1) :

```
Arrivées (λ) → [Station 1: K serveurs] → [Station 2: 1 serveur] → Résultats
                    (exécution tests)        (envoi retour)
```

**Résultats clés** (1000 trajectoires, IC 95%) :
- E[W] = 1.7195 ± 0.0090 (erreur vs théorique: 0.16%)
- Multi-populations: Ratio PREPA/ING = 1.10

**6 modèles** de complexité croissante sont implémentés pour analyser différents scénarios opérationnels.

---

## 🚀 Installation

```bash
# Cloner et se placer dans le dossier
cd ERO2

# Créer l'environnement virtuel
python -m venv venv

# Activer (Windows)
.\venv\Scripts\Activate.ps1
# ou (Linux/Mac)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## ▶️ Exécution

### Lancer tous les modèles

```bash
python tandem_queue_simulation.py    # Modèle de base (validation théorique)
python tandem_queue_finite.py        # Capacités finies (rejets/pertes)
python tandem_queue_backup.py        # Mécanisme de backup
python tandem_queue_populations.py   # Multi-populations ING/PREPA
python tandem_queue_blocking.py      # Blocage périodique (throttling)
python tandem_queue_priority.py      # Politiques de priorité
```

### Exporter les résultats

```bash
python scripts/export_results.py     # Génère les données pour les rapports
```

Les graphiques sont générés dans `img/`.

---

## 📁 Structure du projet

```
ERO2/
├── tandem_queue_simulation.py   # Modèle 1: Files infinies (M/M/K → M/M/1)
├── tandem_queue_finite.py       # Modèle 2: Capacités finies (rejets/pertes)
├── tandem_queue_backup.py       # Modèle 3: Mécanisme de sauvegarde
├── tandem_queue_populations.py  # Modèle 4: ING vs PREPA
├── tandem_queue_blocking.py     # Modèle 5: Throttling périodique
├── tandem_queue_priority.py     # Modèle 6: Politiques de priorité
│
├── utils/
│   └── analysis_utils.py        # Fonctions d'analyse statistique
│
├── scripts/
│   └── export_results.py        # Export des résultats
│
├── reports/                     # Rapports d'analyse détaillés
│   ├── 01_rapport_analyse.md    # Analyse technique complète
│   ├── 02_analyse_stakeholders.md # Facteurs humains et UX
│   ├── 03_recommandations.md    # Guide de dimensionnement
│   ├── 04_donnees_brutes.md     # Résultats bruts des simulations
│   └── 05_synthese_executive.md # Synthèse décisionnelle
│
├── img/                         # Graphiques générés
├── requirements.txt             # Dépendances Python
└── README.md
```

---

## ⚙️ Configuration des paramètres

Chaque script contient une section de paramètres en début de `main()` :

```python
# Paramètres de base
LAMBDA = 4.0      # Taux d'arrivée (jobs/min)
MU1 = 2.0         # Taux de service S1 (par serveur)
MU2 = 5.0         # Taux de service S2
K = 3             # Nombre de serveurs S1

# Paramètres de simulation
N_TRAJECTORIES = 30           # Nombre de simulations
JOBS_PER_TRAJECTORY = 10000   # Jobs par simulation
WARMUP_JOBS = 1000            # Période de chauffe (écartée)
```

### Paramètres spécifiques par modèle

| Modèle | Paramètres clés |
|--------|-----------------|
| **finite** | `ks` (capacité S1), `kf` (capacité S2) |
| **backup** | `backup_prob`, `backup_time_mean`, `max_retries` |
| **populations** | `lambda_ing/prepa`, `mu1_ing/prepa`, `mu2_ing/prepa` |
| **blocking** | `tb` (durée blocage), `block_s1`, `block_s2` |
| **priority** | `policy` (FCFS, SRPT, SEPARATE, PREPA_FIRST) |

---

## 📊 Modèles implémentés

| # | Fichier | Description | Question traitée |
|---|---------|-------------|------------------|
| 1 | `tandem_queue_simulation.py` | Files infinies | Validation théorique |
| 2 | `tandem_queue_finite.py` | Capacités limitées | Taux de rejet/perte |
| 3 | `tandem_queue_backup.py` | Sauvegarde résultats | Élimination pages blanches |
| 4 | `tandem_queue_populations.py` | ING vs PREPA | Équité entre populations |
| 5 | `tandem_queue_blocking.py` | Throttling | Régulation de charge |
| 6 | `tandem_queue_priority.py` | Priorités | Optimisation temps/équité |

---

## 📈 Résultats clés

Les simulations montrent :

- **Goulot d'étranglement** : Station 2 (serveur unique) limite le débit
- **Pages blanches** : ~19% sans backup → 0% avec backup systématique
- **Équité ING/PREPA** : Ratio 1.126 (PREPA +12.6%) → 1.08 avec politique PREPA_FIRST
- **Validation théorique** : Erreur < 0.5% vs formules analytiques

Voir [reports/05_synthese_executive.md](reports/05_synthese_executive.md) pour la synthèse complète.

---

## 📚 Documentation

| Rapport | Contenu |
|---------|---------|
| [01_rapport_analyse.md](reports/01_rapport_analyse.md) | Analyse technique détaillée de chaque modèle |
| [02_analyse_stakeholders.md](reports/02_analyse_stakeholders.md) | Impact utilisateur, métriques UX, risques |
| [03_recommandations.md](reports/03_recommandations.md) | Guide de dimensionnement et configurations |
| [04_donnees_brutes.md](reports/04_donnees_brutes.md) | Tous les résultats numériques |
| [05_synthese_executive.md](reports/05_synthese_executive.md) | Synthèse pour décideurs |

---

## 🔧 Dépendances

```
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.7.0
```

---

## 🎓 Contexte

Projet ERO2 - Recherche Opérationnelle  
EPITA - Janvier 2026
