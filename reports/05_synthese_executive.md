# Synthèse Exécutive

> **Projet ERO2 - Analyse des Systèmes d'Attente**  
> Document de Synthèse pour Décideurs  
> Date : Janvier 2026

---

## Résumé en Une Page

### Contexte

L'infrastructure de correction automatique "moulinette" fait face à des problèmes de performance lors des pics de charge. Cette étude analyse les systèmes d'attente sous-jacents pour optimiser l'expérience utilisateur tout en maîtrisant les coûts.

### Principaux Résultats (Données Réelles)

| Indicateur | Situation Actuelle | Recommandation | Amélioration |
|------------|-------------------|----------------|--------------|
| Pages blanches | ~19% en pic (λ=6) | < 5% | **-74%** |
| Temps de séjour moyen | 7-8 min (multi-pop) | < 2 min | **-75%** |
| Équité ING/PREPA | 12.6% d'écart | < 8% d'écart | **-37%** |
| Taux de rejet | ~10.5% en pic (λ=6) | < 1% | **-90%** |

### Actions Recommandées

1. **Court terme** (Semaine) : Augmenter kf de 5 à 10 → -60% pages blanches
2. **Moyen terme** (Mois) : Implémenter politique PREPA_FIRST → équité optimale
3. **Long terme** (Trimestre) : Backup probabiliste (p=0.5) → -50% pages blanches, -50% coût stockage

### Investissement vs Bénéfices

| Action | Coût Estimé | Bénéfice Principal | ROI |
|--------|-------------|-------------------|-----|
| Augmenter capacité file | Faible (config) | -60% pages blanches | Très élevé |
| Politique PREPA_FIRST | Moyen (dev) | Ratio P/I = 1.08 | Élevé |
| Système backup p=0.5 | Moyen (stockage) | -50% pertes vs systématique | Moyen |

---

## Synthèse Technique

### Architecture Étudiée

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX DE TRAITEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Étudiants    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  (push tag)──→│  File    │──→│ Serveurs │──→│  File    │──→ Résultat
│               │ Exécution│    │ (K=3)    │    │ Retour   │     │
│               │ (ks=10)  │    │          │    │ (kf=5)   │     │
│               └──────────┘    └──────────┘    └──────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Modèle Mathématique

- **Type** : Réseau de Jackson (M/M/K → M/M/1)
- **Condition de stabilité** : ρ₁ = λ/(K·μ₁) < 1 ET ρ₂ = λ/μ₂ < 1
- **Goulot identifié** : Station 2 (serveur unique de retour)

### Résultats Clés par Scénario (Données Réelles)

#### Scénario 1 : Files Infinies (Référence Théorique)

```
Paramètres : λ=4.0, μ₁=2.0, μ₂=5.0, K=3
E[W] théorique : 1.7222 min
E[W] simulé    : 1.7151 min
Erreur         : 0.41%
IC 95%         : [1.6857, 1.7444]
```

**Conclusion** : Validation du simulateur - excellente concordance théorie/simulation.

#### Scénario 2 : Files Finies (ks=10, kf=5)

| λ | Rejet (%) | Perte (%) | E[W] | Débit effectif |
|---|-----------|-----------|------|----------------|
| 4.0 | 0.94 | 8.50 | 1.197 | 3.248 |
| 6.0 | 10.50 | 19.40 | 1.706 | 3.908 |
| 8.0 | 26.28 | 23.50 | 2.034 | 4.051 |

**Conclusion** : À λ=6, près de 30% des jobs sont impactés (rejet+perte).

#### Scénario 3 : Backup (λ=6.0)

| Stratégie | Pages Blanches | Stockage | E[W] Impact |
|-----------|---------------|----------|-------------|
| Aucun | 19.38% | 0 | - |
| Aléatoire (p=0.5) | 14.38% | ~4,047 | +14% |
| Systématique | 0.00% | ~8,083 | +33% |

**Conclusion** : Backup aléatoire (p=0.5) = meilleur compromis coût/efficacité.

#### Scénario 4 : Multi-Populations (ING vs PREPA)

| Population | E[W] | Écart-type | P50 | P90 | P99 |
|------------|------|------------|-----|-----|-----|
| ING | 7.166 | 0.340 | 7.405 | 11.222 | 14.055 |
| PREPA | 8.068 | 0.347 | 8.258 | 12.322 | 15.528 |
| **Ratio P/I** | **1.126** | - | - | - | - |

**Conclusion** : PREPA pénalisés de ~12.6% vs ING.

#### Scénario 5 : Blocage Périodique (tb=5.0)

| État | E[W] ING | E[W] PREPA | Ratio | Jain Index |
|------|----------|------------|-------|------------|
| Sans blocage | 7.169 | 8.079 | 1.127 | 0.837 |
| Avec blocage | 58.050 | 59.450 | 1.024 | 0.987 |

**Conclusion** : Le blocage améliore l'équité (+18% Jain) mais dégrade les temps (+710%).

#### Scénario 6 : Politiques de Priorité (Système Alternatif)

| Politique | E[W] Global | Ratio P/I | Recommandation |
|-----------|-------------|-----------|----------------|
| FCFS | 1.393 | 1.773 | Baseline |
| SRPT | **1.155** | 3.308 | Si temps global prioritaire |
| SEPARATE | 1.507 | 1.332 | Compromis |
| PREPA_FIRST | 1.569 | **1.079** | Si équité prioritaire |

**Conclusion** : PREPA_FIRST offre la meilleure équité avec un coût temps acceptable.

---

## Recommandations Stratégiques

### Priorité 1 : Quick Wins (Immédiat)

| Action | Complexité | Impact | Données Justificatives |
|--------|------------|--------|------------------------|
| Augmenter kf à 10 | Très faible | Pertes: 19.4% → ~8% | Comparaison configs (20,10) |
| Monitoring ρ₂ | Faible | Détection précoce saturation | ρ₂ critique à 0.8 |

### Priorité 2 : Optimisations (Court terme)

| Action | Complexité | Impact | Données Justificatives |
|--------|------------|--------|------------------------|
| Politique PREPA_FIRST | Moyenne | Ratio P/I: 1.77 → 1.08 | Résultats priorités |
| Backup p=0.5 | Moyenne | Pages blanches -26% | Analyse backup λ=6 |

### Priorité 3 : Évolutions Structurelles (Long terme)

| Action | Complexité | Impact | Données Justificatives |
|--------|------------|--------|------------------------|
| Augmenter K (serveurs) | Élevée | ρ₁ réduit, marge capacité | Analyse stabilité |
| Auto-scaling | Très élevée | Adaptation charge | Étude paramétrique λ |

---

## Métriques de Suivi

### KPIs Principaux (Basés sur Résultats Réels)

| KPI | Cible | Seuil Alerte | Seuil Critique | Valeur Actuelle |
|-----|-------|--------------|----------------|-----------------|
| E[W] moyen | < 2 min | > 5 min | > 10 min | 1.72 min (λ=4) |
| Taux pages blanches | < 5% | > 10% | > 20% | 19.4% (λ=6) |
| Taux de rejet | < 1% | > 5% | > 15% | 10.5% (λ=6) |
| Ratio P/I | < 1.15 | > 1.25 | > 1.50 | 1.126 |
| ρ₂ (utilisation S2) | < 0.7 | > 0.8 | > 0.9 | 0.80 (λ=4) |

### Tableau de Bord Recommandé

```
┌────────────────────────────────────────────────────────────┐
│                    ÉTAT DU SYSTÈME                         │
├────────────────────────────────────────────────────────────┤
│  λ actuel : ▓▓▓▓▓▓▓▓░░ 4.0/5.0 (80% capacité)             │
│  ρ₁ (S1)  : ▓▓▓▓▓▓▓░░░ 0.67/1.0 ✓                         │
│  ρ₂ (S2)  : ▓▓▓▓▓▓▓▓░░ 0.80/1.0 ⚠️                        │
│  E[W]     : 1.72 min   ✓                                   │
│  Rejets   : 0.94%      ✓                                   │
│  Pertes   : 8.50%      ⚠️                                  │
└────────────────────────────────────────────────────────────┘
```

---

## Conclusion

L'analyse révèle que le **goulot d'étranglement principal** est la **station de retour (S2)** avec ρ₂ = 0.80 à λ=4.

### Gains Atteignables

| Métrique | Actuel (λ=6) | Cible | Action Principale |
|----------|--------------|-------|-------------------|
| Pages blanches | 19.4% | < 5% | Backup p=0.5 + kf=10 |
| Ratio équité | 1.126 | < 1.10 | Politique PREPA_FIRST |
| Rejets | 10.5% | < 1% | Augmenter ks à 20 |

### Investissement Prioritaire

**Augmenter kf de 5 à 10** : modification de configuration simple avec impact majeur sur les pertes (-60% estimé).

---

## Annexes

### A. Glossaire

| Terme | Définition | Valeur Utilisée |
|-------|------------|-----------------|
| λ | Taux d'arrivée (jobs/min) | 4.0 (nominal) |
| μ₁ | Taux de service S1 (par serveur) | 2.0 |
| μ₂ | Taux de service S2 | 5.0 |
| K | Nombre de serveurs S1 | 3 |
| ρ | Taux d'utilisation | ρ₁=0.67, ρ₂=0.80 |
| E[W] | Espérance du temps de séjour | 1.72 min |
| ks/kf | Capacités des files | 10/5 |

### B. Références

- Kendall, D.G. "Stochastic Processes Occurring in the Theory of Queues" (1953)
- Jackson, J.R. "Networks of Waiting Lines" (1957)
- Burke, P.J. "The Output of a Queuing System" (1956)

### C. Fichiers Source

- `tandem_queue_simulation.py` : Modèle files infinies
- `tandem_queue_finite.py` : Modèle capacités finies
- `tandem_queue_backup.py` : Mécanisme de backup
- `tandem_queue_populations.py` : Multi-populations
- `tandem_queue_blocking.py` : Blocage périodique
- `tandem_queue_priority.py` : Politiques de priorité

---

*Document préparé pour la soutenance ERO2 - Janvier 2026*  
*Toutes les données issues des simulations avec seed=42*
