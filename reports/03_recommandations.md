# Recommandations Opérationnelles et Dimensionnement

> **Projet ERO2 - Recherche Opérationnelle**  
> Guide de Dimensionnement et Configuration  
> Date : Janvier 2026

---

## Table des Matières

1. [Synthèse Exécutive](#1-synthèse-exécutive)
2. [Guide de Dimensionnement](#2-guide-de-dimensionnement)
3. [Configurations Recommandées](#3-configurations-recommandées)
4. [Procédures Opérationnelles](#4-procédures-opérationnelles)
5. [Indicateurs de Performance](#5-indicateurs-de-performance)
6. [Plan d'Action](#6-plan-daction)

---

## 1. Synthèse Exécutive

### 1.1 Conclusions Principales

| Aspect | Constat | Recommandation |
|--------|---------|----------------|
| **Goulot d'étranglement** | Station 2 (serveur unique) | Augmenter μ₂ ou kf |
| **Pages blanches** | 19% sans backup | Backup p=0.5 minimum |
| **Équité ING/PREPA** | PREPA +10% | Politique PREPA_FIRST |
| **Pics de charge** | Système saturé | Throttling préventif |

### 1.2 Paramètres Critiques

Les trois paramètres ayant le plus d'impact :

1. **λ (charge)** : À surveiller en temps réel
2. **kf (capacité S2)** : Détermine le taux de perte
3. **Backup** : Détermine les pages blanches

### 1.3 Quick Wins

| Action | Effort | Impact | Priorité |
|--------|--------|--------|----------|
| Activer backup p=0.5 | Faible | -30% pages blanches | ⭐⭐⭐ |
| Augmenter kf à 10 | Faible | -50% pertes | ⭐⭐⭐ |
| Dashboard temps réel | Moyen | Réactivité | ⭐⭐ |
| Politique PREPA_FIRST | Moyen | Ratio équité 1.08 | ⭐⭐ |

---

## 2. Guide de Dimensionnement

### 2.1 Estimation de la Charge

#### Formule d'Estimation

$$\lambda_{estimé} = N_{étudiants} \times f_{activité} \times r_{soumission}$$

Où :
- $N_{étudiants}$ : Nombre d'étudiants actifs simultanément
- $f_{activité}$ : Facteur d'activité (0.3 normal, 0.7 projet, 1.0 deadline)
- $r_{soumission}$ : Taux de soumission moyen (0.1 jobs/min/étudiant actif)

#### Table de Référence

| Contexte | N_étudiants | f_activité | λ estimé |
|----------|-------------|------------|----------|
| TP standard | 30 | 0.3 | 0.9 |
| TP chargé | 50 | 0.5 | 2.5 |
| Projet normal | 80 | 0.5 | 4.0 |
| Projet intense | 100 | 0.7 | 7.0 |
| Deadline | 150 | 1.0 | 15.0 |

### 2.2 Dimensionnement de K (Serveurs S1)

#### Règle de Base

$$K \geq \left\lceil \frac{\lambda_{max}}{0.8 \times \mu_1} \right\rceil$$

**Objectif** : Maintenir ρ₁ < 80% pour avoir une marge de manœuvre.

#### Table de Dimensionnement

| λ_max | μ₁ = 1.0 | μ₁ = 2.0 | μ₁ = 3.0 |
|-------|----------|----------|----------|
| 2.0 | K ≥ 3 | K ≥ 2 | K ≥ 1 |
| 4.0 | K ≥ 5 | K ≥ 3 | K ≥ 2 |
| 6.0 | K ≥ 8 | K ≥ 4 | K ≥ 3 |
| 10.0 | K ≥ 13 | K ≥ 7 | K ≥ 5 |

### 2.3 Dimensionnement de μ₂ (Station 2)

#### Contrainte Fondamentale

$$\mu_2 > \lambda_{max} \times 1.25$$

**Justification** : Marge de 25% pour absorber les variations.

#### Impact sur les Performances

| μ₂ | λ_max stable | E[W₂] pour λ=4 | Recommandation |
|----|--------------|----------------|----------------|
| 4.5 | 4.5 | 2.22 | Insuffisant |
| 5.0 | 5.0 | 1.00 | Minimum |
| 6.0 | 6.0 | 0.50 | Recommandé |
| 8.0 | 8.0 | 0.25 | Optimal |

### 2.4 Dimensionnement des Capacités (ks, kf)

#### Règles de Dimensionnement

| Capacité | Règle | Justification |
|----------|-------|---------------|
| ks | K + 2×E[Lq₁] | File + serveurs + marge |
| kf | 1 + 3×E[Lq₂] | Serveur + file + marge |

#### Table de Référence (μ₁=2, μ₂=5, K=3)

| λ | ks recommandé | kf recommandé | Config suggérée |
|---|---------------|---------------|-----------------|
| 2.0 | 5 | 3 | (5, 3) |
| 4.0 | 10 | 5 | (10, 5) |
| 6.0 | 20 | 10 | (20, 10) |
| 8.0 | 35 | 15 | (35, 15) |
| 10.0 | 50 | 20 | (50, 20) |

### 2.5 Nomogramme de Dimensionnement

```
λ (charge)
    │
    │ 10+ ─────────────────────────────── Config MAXIMALE
    │     │                               K≥7, ks≥50, kf≥20
    │  8  ─────────────────────────────── Backup systématique
    │     │                               Throttling recommandé
    │  6  ─────────────────────────────── Config RENFORCÉE
    │     │                               K≥4, ks≥20, kf≥10
    │  4  ─────────────────────────────── Backup aléatoire p=0.5
    │     │
    │  3  ─────────────────────────────── Config STANDARD
    │     │                               K=3, ks=10, kf=5
    │  2  ─────────────────────────────── 
    │     │
    │  0  ─────────────────────────────── Config MINIMALE
    └──────────────────────────────────────────────────────
```

---

## 3. Configurations Recommandées

### 3.1 Configuration STANDARD

**Contexte** : Usage quotidien, charge modérée (λ < 4)

```yaml
infrastructure:
  K: 3                    # Serveurs exécution
  mu1: 2.0                # Taux service S1
  mu2: 5.0                # Taux service S2
  
capacites:
  ks: 10                  # Capacité S1
  kf: 5                   # Capacité S2
  
mecanismes:
  backup: false
  throttling: false
  
seuils_alerte:
  lambda_warn: 3.0
  lambda_critical: 4.0
  E_W_warn: 3.0
  E_W_critical: 5.0
```

**Performances attendues** (λ = 3.0) :
- E[W] ≈ 1.2 min
- Taux de rejet < 1%
- Taux de perte < 3%

### 3.2 Configuration RENFORCÉE

**Contexte** : Projets, rendus, charge élevée (4 ≤ λ < 7)

```yaml
infrastructure:
  K: 4                    # +1 serveur
  mu1: 2.0
  mu2: 5.0
  
capacites:
  ks: 20                  # Doublé
  kf: 10                  # Doublé
  
mecanismes:
  backup: true
  backup_probability: 0.5
  backup_time: 0.1
  throttling: false
  
seuils_alerte:
  lambda_warn: 5.0
  lambda_critical: 7.0
  E_W_warn: 5.0
  E_W_critical: 10.0
```

**Performances attendues** (λ = 5.0) :
- E[W] ≈ 2.5 min
- Taux de rejet < 5%
- Taux de perte < 5% (pages blanches < 3%)

### 3.3 Configuration MAXIMALE

**Contexte** : Deadline critique, surcharge (λ ≥ 7)

```yaml
infrastructure:
  K: 6                    # Maximum
  mu1: 2.0
  mu2: 5.0
  
capacites:
  ks: 50
  kf: 20
  
mecanismes:
  backup: true
  backup_probability: 1.0  # Systématique
  throttling: true
  tb: 2.0                  # 2 min fermé
  t_open: 1.0              # 1 min ouvert
  
seuils_alerte:
  lambda_warn: 8.0
  lambda_critical: 12.0
  E_W_warn: 10.0
  E_W_critical: 20.0
```

**Performances attendues** (λ = 10.0, avec throttling) :
- E[W] ≈ 15 min (acceptable vu le contexte)
- Taux de rejet ≈ 20% (communiqué aux étudiants)
- Taux de perte < 1% (backup systématique)
- Pages blanches ≈ 0%

### 3.4 Configuration ÉQUITÉ (Alternative)

**Contexte** : Populations hétérogènes, priorité à l'équité

```yaml
infrastructure:
  K: 3
  politique: PREPA_FIRST  # Priorité aux PREPA pour compenser
  
populations:
  ING:
    mu1: 4.0
    mu2: 8.0
  PREPA:
    mu1: 1.0
    mu2: 3.0
    priorite: HIGH  # Compensation du temps de service plus long
    
mecanismes:
  backup: true
  backup_probability: 0.5
```

**Performances attendues** (basé sur simulation) :
- Ratio E[W]_PREPA / E[W]_ING ≈ 1.08 (équité optimale)
- E[W] global = 1.57 (légère augmentation acceptable)

---

## 4. Procédures Opérationnelles

### 4.1 Procédure de Montée en Charge

```
┌─────────────────────────────────────────────────────────────┐
│                 PROCÉDURE DE MONTÉE EN CHARGE               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DÉTECTION (Automatique)                                 │
│     ├─ λ > seuil_warn pendant 5 min                        │
│     └─ Alerte dashboard                                     │
│                                                             │
│  2. ÉVALUATION (Opérateur)                                  │
│     ├─ Vérifier cause (deadline? incident?)                │
│     └─ Estimer durée                                        │
│                                                             │
│  3. ACTION (Selon niveau)                                   │
│     ├─ λ ∈ [warn, critical] → Activer backup               │
│     └─ λ > critical → Throttling + Communication           │
│                                                             │
│  4. COMMUNICATION                                           │
│     ├─ Dashboard : "Charge élevée"                         │
│     ├─ Si throttling : Message étudiants                   │
│     └─ Si deadline : Coordination enseignants              │
│                                                             │
│  5. SURVEILLANCE                                            │
│     └─ Monitorer jusqu'à retour normal                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Procédure de Gestion de Crise

```
┌─────────────────────────────────────────────────────────────┐
│                   PROCÉDURE DE CRISE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NIVEAU 1 : DÉGRADATION (E[W] > 10 min)                    │
│  ────────────────────────────────────                       │
│  □ Activer backup systématique                             │
│  □ Activer throttling tb=2min                              │
│  □ Message dashboard "Service dégradé"                     │
│  □ Prévenir équipe pédagogique                             │
│                                                             │
│  NIVEAU 2 : SURCHARGE (Taux rejet > 30%)                   │
│  ────────────────────────────────────                       │
│  □ Augmenter tb à 5min                                     │
│  □ Email aux étudiants concernés                           │
│  □ Évaluer extension deadline                              │
│  □ Activer serveurs de backup si disponibles              │
│                                                             │
│  NIVEAU 3 : PANNE (Indisponibilité)                        │
│  ────────────────────────────────────                       │
│  □ Basculer sur infrastructure backup                      │
│  □ Communication tous canaux                               │
│  □ Hotline support active                                  │
│  □ Post-mortem prévu                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Checklist Avant Deadline

```
□ J-7  : Vérifier configuration (renforcée ou maximale)
□ J-3  : Tester backup et throttling
□ J-1  : Communication préventive aux étudiants
□ J-1  : Vérifier disponibilité équipe support
□ H-2  : Activation configuration maximale
□ H-2  : Surveillance temps réel active
□ H    : Deadline - monitoring critique
□ H+1  : Retour configuration standard si charge normale
```

---

## 5. Indicateurs de Performance (KPIs)

### 5.1 KPIs Temps Réel

| KPI | Formule | Seuil Vert | Seuil Orange | Seuil Rouge |
|-----|---------|------------|--------------|-------------|
| Charge | λ mesuré (jobs/min) | < 3 | 3-5 | > 5 |
| Temps réponse | E[W] moyen (min) | < 2 | 2-5 | > 5 |
| File S1 | Lq₁ / ks (%) | < 50% | 50-80% | > 80% |
| File S2 | Lq₂ / kf (%) | < 50% | 50-80% | > 80% |

### 5.2 KPIs Journaliers

| KPI | Formule | Objectif | Alerte si |
|-----|---------|----------|-----------|
| Disponibilité | Uptime / 24h | > 99.5% | < 99% |
| Taux de rejet global | Rejets / Arrivées | < 2% | > 5% |
| Taux de perte global | Pertes / Traités | < 1% | > 3% |
| Pages blanches | Pertes sans backup / Traités | < 0.5% | > 2% |

### 5.3 KPIs Hebdomadaires/Mensuels

| KPI | Description | Objectif |
|-----|-------------|----------|
| Pic de charge max | Max(λ) sur la période | Document pour dimensionnement |
| P99 temps réponse | 99ème percentile de W | < 15 min |
| Satisfaction estimée | Score calculé | > 70% |
| Incidents | Nombre de crises niveau 2+ | 0 |

### 5.4 Dashboard Recommandé

```
╔═══════════════════════════════════════════════════════════════════╗
║  MOULINETTE MONITORING                            [🟢 OPÉRATIONNEL]║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  📊 MÉTRIQUES TEMPS RÉEL                    ⏰ Dernière MAJ: 14:32║
║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ║
║  │  λ = 3.2    │ │ E[W] = 1.8  │ │ S1: 4/10   │ │ S2: 2/5     │ ║
║  │  jobs/min   │ │    min      │ │    40%     │ │    40%      │ ║
║  │    🟢       │ │    🟢       │ │    🟢      │ │    🟢       │ ║
║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ ║
║                                                                   ║
║  📈 DERNIÈRE HEURE                                               ║
║  ┌───────────────────────────────────────────────────────────┐   ║
║  │ Arrivées: 192  │ Complétés: 188  │ Rejetés: 3  │ Perdus: 1│   ║
║  │ Taux rejet: 1.6%│ Taux perte: 0.5%│ Pages blanches: 0   │   ║
║  └───────────────────────────────────────────────────────────┘   ║
║                                                                   ║
║  ⚙️ CONFIGURATION ACTIVE                                         ║
║  [✓ Standard] [ Renforcée] [ Maximale]                          ║
║  Backup: OFF  │  Throttling: OFF  │  Files: FIFO               ║
║                                                                   ║
║  [📊 Historique] [⚙️ Configuration] [📧 Alertes] [📄 Rapports]  ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 6. Plan d'Action

### 6.1 Actions Immédiates (Cette Semaine)

| # | Action | Responsable | Effort | Impact |
|---|--------|-------------|--------|--------|
| 1 | Implémenter backup p=0.5 | Admin | 2h | -30% pages blanches |
| 2 | Configurer alertes seuils | Admin | 1h | Réactivité |
| 3 | Documenter procédures | Équipe | 4h | Qualité |

### 6.2 Actions Court Terme (Ce Mois)

| # | Action | Responsable | Effort | Impact |
|---|--------|-------------|--------|--------|
| 4 | Dashboard temps réel | Dev | 2j | Visibilité |
| 5 | Tests de charge | Admin | 1j | Validation |
| 6 | Formation équipe | Manager | 4h | Compétences |

### 6.3 Actions Moyen Terme (Ce Semestre)

| # | Action | Responsable | Effort | Impact |
|---|--------|-------------|--------|--------|
| 7 | Politique PREPA_FIRST | Dev | 1sem | Ratio équité 1.08 |
| 8 | Auto-scaling | Infra | 2sem | Élasticité |
| 9 | Analytics avancés | Data | 1sem | Insights |

### 6.4 Critères de Succès

| Objectif | Métrique | Cible | Échéance |
|----------|----------|-------|----------|
| Fiabilité | Pages blanches | < 0.5% | 1 mois |
| Performance | P95(W) | < 5 min | 1 mois |
| Disponibilité | Uptime | > 99.9% | 3 mois |
| Équité | Ratio P/I | < 1.10 | 6 mois |

---

## Annexe : Formules de Référence

### Formules de Dimensionnement

$$K_{min} = \left\lceil \frac{\lambda}{0.8 \times \mu_1} \right\rceil$$

$$\mu_{2,min} = 1.25 \times \lambda_{max}$$

$$k_s = K + 2 \times \frac{\lambda \times P_Q}{K \times \mu_1 - \lambda}$$

$$k_f = 1 + 3 \times \frac{\lambda}{\mu_2 - \lambda}$$

### Formules de Performance

$$E[W] = E[W_1] + E[W_2]$$

$$E[W_1] = \frac{P_Q}{K \mu_1 - \lambda} + \frac{1}{\mu_1}$$

$$E[W_2] = \frac{1}{\mu_2 - \lambda}$$

### Formule de Satisfaction

$$\text{Score} = 100 - 10 \times E[W] - 50 \times P_{loss} - 30 \times P_{reject}$$

---

*Document de référence pour l'exploitation de la moulinette*
