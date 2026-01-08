# Analyse des Parties Prenantes et Impact Utilisateur

> **Projet ERO2 - Recherche Opérationnelle**  
> Facteurs Humains et Organisationnels  
> Date : Janvier 2026

---

## Table des Matières

1. [Identification des Parties Prenantes](#1-identification-des-parties-prenantes)
2. [Analyse des Besoins par Acteur](#2-analyse-des-besoins-par-acteur)
3. [Métriques UX et Seuils Acceptables](#3-métriques-ux-et-seuils-acceptables)
4. [Analyse des Risques](#4-analyse-des-risques)
5. [Scénarios d'Usage](#5-scénarios-dusage)
6. [Recommandations Contextualisées](#6-recommandations-contextualisées)

---

## 1. Identification des Parties Prenantes

### 1.1 Cartographie des Acteurs

```
                    ┌───────────────────┐
                    │   DIRECTION       │
                    │   PÉDAGOGIQUE     │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   ENSEIGNANTS   │ │ ADMINISTRATEURS │ │   ÉTUDIANTS     │
│   (Concepteurs) │ │    (Infra)      │ │  (Utilisateurs) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │    SYSTÈME        │
                    │   MOULINETTE      │
                    └───────────────────┘
```

### 1.2 Profils des Acteurs

| Acteur | Rôle | Objectif Principal |
|--------|------|-------------------|
| **Étudiants** | Utilisateurs finaux | Obtenir un feedback rapide et fiable |
| **Enseignants** | Concepteurs d'activités | Évaluer équitablement, éviter la triche |
| **Admin Infra** | Gestionnaires techniques | Maintenir la disponibilité, optimiser les coûts |
| **Direction** | Pilotage stratégique | Qualité pédagogique, image de l'école |

---

## 2. Analyse des Besoins par Acteur

### 2.1 Étudiants

#### Besoins Fonctionnels

| Besoin | Priorité | Métrique associée |
|--------|----------|-------------------|
| Feedback rapide | Haute | E[W] < 5 minutes |
| Résultat toujours disponible | Haute | Taux de perte < 1% |
| Équité de traitement | Moyenne | Variance(W) faible |
| Transparence sur l'attente | Moyenne | Estimation temps affichée |

#### Frustrations Potentielles

| Situation | Impact Émotionnel | Fréquence Acceptable |
|-----------|-------------------|----------------------|
| Push tag rejeté | Frustration modérée | < 5% des soumissions |
| Page blanche | Frustration forte | < 1% des soumissions |
| Attente > 10 min | Anxiété | < 10% des soumissions |
| Attente > 30 min | Abandon potentiel | Jamais |

#### Verbatims Typiques (simulés)

> *"J'ai attendu 15 minutes et j'ai eu une page blanche, c'est inacceptable avant un rendu !"*

> *"Mon camarade a eu son résultat en 2 minutes et moi j'attends depuis 10 minutes, c'est injuste."*

### 2.2 Enseignants

#### Besoins Fonctionnels

| Besoin | Priorité | Métrique associée |
|--------|----------|-------------------|
| Évaluation équitable | Haute | Ratio temps par population ≈ 1 |
| Limiter le "bruteforce" | Haute | Quotas respectés |
| Feedback pédagogique adapté | Moyenne | Niveau d'info configurable |
| Statistiques d'utilisation | Basse | Dashboard disponible |

#### Contraintes Pédagogiques

| Contrainte | Impact sur le système |
|------------|----------------------|
| Deadline stricte | Pic de charge prévisible |
| Rendu noté | Nécessité de fiabilité maximale |
| TP exploratoire | Tolérance plus élevée aux erreurs |

### 2.3 Administrateurs Infrastructure

#### Besoins Fonctionnels

| Besoin | Priorité | Métrique associée |
|--------|----------|-------------------|
| Disponibilité 99.9% | Haute | Uptime |
| Coût maîtrisé | Moyenne | Ressources utilisées |
| Maintenance possible | Moyenne | Fenêtre de blocage |
| Scalabilité | Basse | Capacité d'extension |

#### Contraintes Opérationnelles

| Contrainte | Période | Action |
|------------|---------|--------|
| Maintenance serveurs | Nuit | Blocage planifié |
| Mise à jour sécurité | Urgente | Blocage immédiat |
| Ajout capacité | Prévu | Déploiement progressif |

### 2.4 Direction Pédagogique

#### Besoins Fonctionnels

| Besoin | Priorité | Métrique associée |
|--------|----------|-------------------|
| Image de qualité | Haute | Satisfaction étudiants |
| Efficacité pédagogique | Haute | Taux de réussite |
| Innovation | Moyenne | Fonctionnalités avancées |

---

## 3. Métriques UX et Seuils Acceptables

### 3.1 Temps de Réponse Acceptable

Basé sur des études UX standard (Nielsen Norman Group) :

| Seuil | Perception Utilisateur | Acceptable pour |
|-------|------------------------|-----------------|
| < 1 sec | Instantané | Feedback syntaxique |
| 1-10 sec | Attente supportable | Test unitaire simple |
| 10 sec - 1 min | Attention diminue | Test complet standard |
| 1-5 min | Frustration naissante | Test long (acceptable) |
| > 5 min | Abandon probable | Inacceptable en routine |

### 3.2 Seuils Recommandés pour la Moulinette

| Métrique | Seuil Optimal | Seuil Acceptable | Seuil Critique |
|----------|---------------|------------------|----------------|
| E[W] | < 2 min | < 5 min | > 10 min |
| P(W > 10 min) | < 5% | < 15% | > 30% |
| Taux de rejet | < 1% | < 5% | > 15% |
| Taux de perte | < 0.1% | < 1% | > 5% |
| Disponibilité | > 99.9% | > 99% | < 95% |

### 3.3 Indice de Satisfaction Estimé

Formule proposée (inspirée de CSAT) :

$$\text{Satisfaction} = 100 - 10 \times E[W]_{min} - 50 \times P_{loss} - 30 \times P_{reject}$$

| Situation | E[W] | P_loss | P_reject | Score |
|-----------|------|--------|----------|-------|
| Optimale | 1.5 | 0% | 0% | 85% |
| Normale | 3.0 | 1% | 2% | 68.5% |
| Dégradée | 5.0 | 5% | 10% | 44.5% |
| Critique | 10.0 | 10% | 20% | -1% |

**Interprétation** :
- Score > 70% : Satisfaction élevée
- Score 50-70% : Satisfaction acceptable
- Score < 50% : Insatisfaction significative

---

## 4. Analyse des Risques

### 4.1 Matrice des Risques

| Risque | Probabilité | Impact | Criticité | Mitigation |
|--------|-------------|--------|-----------|------------|
| Pic de charge deadline | Élevée | Fort | **CRITIQUE** | Throttling préventif |
| Panne serveur | Faible | Fort | MODÉRÉ | Redondance |
| Page blanche récurrente | Moyenne | Fort | **CRITIQUE** | Backup systématique |
| Temps excessif PREPA | Moyenne | Moyen | MODÉRÉ | Files séparées |
| Bruteforce test-suite | Élevée | Moyen | MODÉRÉ | Quotas stricts |

### 4.2 Risques par Phase du Semestre

```
Impact
  ▲
  │    ████
  │   █████    ████
  │  ██████   ██████   ████
  │ ████████ ████████ ██████
  │██████████████████████████
  └────────────────────────────► Temps
    Début   Mi-semestre  Deadline
```

| Phase | Niveau de Risque | Action Préventive |
|-------|------------------|-------------------|
| Début semestre | Faible | Configuration standard |
| Mi-semestre | Moyen | Surveillance accrue |
| Avant deadline | **Élevé** | Throttling, backup systématique |
| Pendant deadline | **Critique** | Capacité maximale, support actif |

### 4.3 Scénarios de Crise

#### Scénario 1 : Surcharge Deadline

**Contexte** : 200 étudiants soumettent simultanément 2h avant deadline

**Impact sans mesures** :
- λ estimé : 15-20 jobs/min (vs capacité 5 jobs/min)
- Taux de rejet : > 60%
- E[W] : > 30 min
- Pages blanches : > 30%

**Mesures de mitigation** :
1. Activer throttling tb=2min (disponibilité 33%)
2. Message proactif aux étudiants
3. Extension deadline si nécessaire

#### Scénario 2 : Panne Serveur Station 2

**Contexte** : Le serveur d'affichage tombe pendant 30 min

**Impact** :
- Toutes les soumissions en cours perdues
- Accumulation de K×λ×30 = 360 jobs

**Mesures de mitigation** :
1. Backup systématique activé avant
2. Restauration automatique depuis backup
3. Communication immédiate

### 4.4 Plan de Communication de Crise

| Situation | Canal | Message Type | Délai |
|-----------|-------|--------------|-------|
| Dégradation | Dashboard | "Temps d'attente élevé" | Immédiat |
| Rejet fréquent | Email | "Système chargé, réessayez" | 5 min |
| Page blanche | Slack/Discord | "Incident en cours, backup actif" | 10 min |
| Panne totale | Tous canaux | "Maintenance urgente, ETA: Xh" | 15 min |

---

## 5. Scénarios d'Usage

### 5.1 Scénario A : TP Standard (Sans Pression)

**Profil** : Semaine normale, 50 étudiants actifs, λ = 2 jobs/min

| Métrique | Attendu | Acceptable |
|----------|---------|------------|
| E[W] | 1.0 min | < 2 min |
| Taux rejet | 0% | < 1% |
| Taux perte | 0% | < 0.5% |

**Configuration recommandée** :
- Standard (K=3, ks=10, kf=5)
- Backup désactivé
- Pas de throttling

### 5.2 Scénario B : Projet Noté (Pression Modérée)

**Profil** : Rendu dans 24h, 100 étudiants actifs, λ = 6 jobs/min

| Métrique | Attendu | Acceptable |
|----------|---------|------------|
| E[W] | 3.0 min | < 5 min |
| Taux rejet | 5% | < 10% |
| Taux perte | 1% | < 3% |

**Configuration recommandée** :
- Capacité augmentée (ks=20, kf=10)
- Backup aléatoire p=0.5
- Surveillance active

### 5.3 Scénario C : Deadline Critique

**Profil** : 2h avant deadline, 200 étudiants, λ = 15 jobs/min

| Métrique | Attendu | Acceptable |
|----------|---------|------------|
| E[W] | 10 min | < 20 min |
| Taux rejet | 30% | < 50% |
| Taux perte | 0% | < 1% |

**Configuration recommandée** :
- Capacité maximale (ks=50, kf=20)
- Backup systématique
- Throttling tb=2min
- Communication proactive

### 5.4 Matrice de Décision

```
                    Pression faible    Pression moyenne    Pression forte
                    ───────────────    ────────────────    ──────────────
Configuration       Standard           Renforcée           Maximale
Backup             Désactivé          Aléatoire (0.5)     Systématique
Throttling         Non                Optionnel           Oui
Surveillance       Passive            Active              Continue
Communication      Aucune             Dashboard           Proactive
```

---

## 6. Recommandations Contextualisées

### 6.1 Pour les Étudiants

| Recommandation | Justification | Bénéfice |
|----------------|---------------|----------|
| Soumettre régulièrement | Éviter accumulation finale | -50% d'attente |
| Éviter les heures de pointe | File plus courte | -30% d'attente |
| Ne pas spammer | Respecter les quotas | Pas de blocage |
| Préparer code avant soumission | Réduire rejets | Moins de frustration |

**Heures recommandées** (basé sur les patterns d'usage) :
- ✅ 8h-10h (faible affluence)
- ✅ 14h-16h (modéré)
- ⚠️ 18h-22h (pic standard)
- ❌ 22h-2h veille deadline (saturé)

### 6.2 Pour les Enseignants

| Recommandation | Contexte | Impact |
|----------------|----------|--------|
| Définir quotas adaptés | Toujours | Limite le bruteforce |
| Prévoir deadline en journée | Projets importants | Permet intervention |
| Communiquer sur les pics | Avant deadline | Réduit la charge |
| Test-suite progressive | TP exploratoire | Feedback rapide |

**Stratégie de quotas recommandée** :

| Type d'activité | Quotas/heure | Total | Justification |
|-----------------|--------------|-------|---------------|
| TP exploratoire | Illimité | 50 | Apprentissage libre |
| Projet standard | 5 | 30 | Limite bruteforce |
| Examen | 3 | 10 | Évaluation réelle |

### 6.3 Pour les Administrateurs

| Recommandation | Trigger | Action |
|----------------|---------|--------|
| Monitoring temps réel | λ > 4 | Alerte dashboard |
| Activation backup | P_loss > 5% | Backup p=0.5 |
| Activation throttling | λ > 8 | tb = 2 min |
| Ajout capacité | λ soutenu > 6 | Serveur supplémentaire |

**Tableau de bord recommandé** :

```
┌────────────────────────────────────────────────────────────┐
│  MOULINETTE DASHBOARD                         [🟢 NORMAL] │
├────────────────────────────────────────────────────────────┤
│  λ actuel: 3.2 jobs/min    │  E[W] actuel: 1.8 min       │
│  Files S1: 4/10            │  Files S2: 2/5              │
│  Rejets (1h): 2 (0.4%)     │  Pertes (1h): 0 (0.0%)      │
├────────────────────────────────────────────────────────────┤
│  [⚙️ Backup: OFF] [⚙️ Throttling: OFF] [📊 Stats] [🔧 Config]│
└────────────────────────────────────────────────────────────┘
```

### 6.4 Synthèse des Seuils d'Alerte

| Niveau | Indicateur | Action Automatique | Action Manuelle |
|--------|------------|-------------------|-----------------|
| 🟢 Normal | λ < 3, E[W] < 2 | Aucune | Aucune |
| 🟡 Attention | 3 < λ < 5, E[W] < 5 | Alerte dashboard | Surveillance |
| 🟠 Alerte | 5 < λ < 8, E[W] < 10 | Backup auto | Préparer throttling |
| 🔴 Critique | λ > 8, E[W] > 10 | Throttling auto | Communication |

---

## Conclusion

L'analyse des parties prenantes révèle des besoins parfois contradictoires :

- **Étudiants** : Rapidité et fiabilité
- **Enseignants** : Équité et contrôle
- **Admin** : Stabilité et coût

La solution optimale nécessite une **approche contextuelle** :
1. Configuration dynamique selon la charge
2. Communication proactive lors des pics
3. Mécanismes de protection automatiques (backup, throttling)

**L'équilibre recommandé** priorise :
1. Fiabilité (pages blanches < 1%) - Non négociable
2. Disponibilité (rejet < 5%) - Haute priorité
3. Rapidité (E[W] < 5 min) - Objectif standard
4. Équité (ratio P/I < 1.2) - Souhaitable

---

*Document préparé pour la soutenance ERO2*
