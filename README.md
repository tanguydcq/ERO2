# ERO2 - Analyse des Systèmes d'Attente

> Simulation d'une infrastructure de correction automatique ("moulinette")  

---

## 📋 Contexte

Ce projet analyse le comportement d'un système de correction automatique sous l'angle des **files d'attente (Queueing Theory)**. Le système est modélisé comme un réseau tandem M/M/K → M/M/1 :

```
Arrivées (λ) → [Station 1: K serveurs] → [Station 2: 1 serveur] → Résultats
                   (exécution tests)         (envoi retour)
```

---

## 📁 Structure du Rendu

### Code (`*.py`)

| Fichier | Description |
|---------|-------------|
| `tandem_queue_simulation.py` | Modèle de base - Files infinies |
| `tandem_queue_finite.py` | Files finies avec rejets |
| `tandem_queue_backup.py` | Mécanisme de back-up |
| `tandem_queue_populations.py` | Multi-populations (ING/PREPA) |
| `tandem_queue_blocking.py` | Blocage et throttling |
| `tandem_queue_priority.py` | Politiques de priorité |
| `utils/analysis_utils.py` | Fonctions d'analyse (IC, stabilité) |
| `optimization/parameter_optimization.py` | Optimisation des paramètres |
| `scripts/generate_results_1000traj.py` | Génération des résultats (1000 traj) |
| `scripts/generate_all_models.py` | Génération tous modèles |
| `scripts/export_results.py` | Export CSV/JSON |

### Analyse (`reports/`)

| Rapport | Contenu |
|---------|---------|
| `01_rapport_analyse.md` | Analyse technique complète (paramètres, stabilité, métriques) |
| `02_analyse_stakeholders.md` | Facteurs humains et organisationnels |
| `03_recommandations.md` | Préconisations et dimensionnement |
| `04_donnees_brutes.md` | Données brutes des simulations |
| `05_synthese_executive.md` | Synthèse décisionnelle |

### Données (`data/`)

| Dossier | Contenu |
|---------|---------|
| `results_1000traj/` | Résultats 1000 trajectoires (CSV, JSON) |
| `all_models_results/` | Résultats tous modèles |

### Graphiques (`img/`)

14 graphiques d'analyse générés automatiquement.

### Notebook (`notebooks/`)

| Fichier | Description |
|---------|-------------|
| `demo_interactive.ipynb` | Démonstration interactive des simulations |

---

## ▶️ Exécution

```bash
# Installation
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# Lancer les simulations
python tandem_queue_simulation.py    # Files infinies
python tandem_queue_finite.py        # Capacités finies
python tandem_queue_backup.py        # Backup
python tandem_queue_populations.py   # Multi-populations
python tandem_queue_blocking.py      # Throttling
python tandem_queue_priority.py      # Priorités

# Générer tous les résultats (1000 trajectoires)
python scripts/generate_results_1000traj.py
python scripts/generate_all_models.py
```

---

## 📊 Résultats Clés

**Méthodologie** : 1000 trajectoires, 5000 jobs/trajectoire, IC 95% (Student-t)

| Métrique | Valeur | IC 95% |
|----------|--------|--------|
| E[W] files infinies | 1.7195 | ±0.0090 |
| E[W] ING | 2.8363 | - |
| E[W] PREPA | 3.1124 | - |
| Ratio PREPA/ING | 1.10 | - |
| Erreur vs théorique | 0.16% | - |

**Cas d'étude traités** :
1. **Waterfall** : Files infinies → Files finies → Backup
2. **Channels & Dams** : Multi-populations → Throttling → Politiques alternatives

---

## 🎯 Correspondance avec la Grille d'Évaluation

| Indicateur | Éléments fournis |
|------------|------------------|
| **Démarche itérative avec métriques** | 1000 trajectoires, IC 95%, comparaison théorique |
| **Analyse des limites** | Périmètre de validité (ρ<1), comportement vs M/M/K théorique |
| **Facteurs externes** | Analyse UX, équité ING/PREPA, recommandations opérationnelles |

---

## 🔧 Dépendances

```
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.7.0
seaborn>=0.11.0
```
