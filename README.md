# ERO2 - Analyse des Systèmes d'Attente

**Auteurs :**

- Tanguy Ducrocq
- Quentin Gillet
- Luke Goboyan
- Pierre Lavielle
- Guillaume Rodriguez
- Louis Romain

## Structure du Rendu

### Code (`*.py`)

| Fichier                                  | Description                           |
| ---------------------------------------- | ------------------------------------- |
| `dashboard.py`                           | Dashboard interactif de visualisation |
| `tandem_queue_simulation.py`             | Modèle de base - Files infinies       |
| `tandem_queue_finite.py`                 | Files finies avec rejets              |
| `tandem_queue_backup.py`                 | Mécanisme de back-up                  |
| `tandem_queue_populations.py`            | Multi-populations (ING/PREPA)         |
| `tandem_queue_blocking.py`               | Blocage et throttling                 |
| `tandem_queue_priority.py`               | Politiques de priorité                |
| `utils/analysis_utils.py`                | Fonctions d'analyse (IC, stabilité)   |
| `optimization/parameter_optimization.py` | Optimisation des paramètres           |
| `scripts/generate_results_1000traj.py`   | Génération des résultats (1000 traj)  |
| `scripts/generate_all_models.py`         | Génération tous modèles               |
| `scripts/export_results.py`              | Export CSV/JSON                       |

### Données (`data/`)

| Dossier               | Contenu                                 |
| --------------------- | --------------------------------------- |
| `results_1000traj/`   | Résultats 1000 trajectoires (CSV, JSON) |
| `all_models_results/` | Résultats tous modèles                  |

### Graphiques (`img/generated/`)

14 graphiques d'analyse générés automatiquement.

### Notebook (`notebooks/`)

| Fichier                  | Description                               |
| ------------------------ | ----------------------------------------- |
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

# Lancer le dashboard
streamlit run dashboard.py

# Générer tous les résultats (1000 trajectoires)
python scripts/generate_results_1000traj.py
python scripts/generate_all_models.py
```
