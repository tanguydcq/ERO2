# Vérification de Conformité - Grille d'Évaluation ERO2

> **Objectif** : Vérifier que le projet répond aux critères "Dépasse les attentes" ou "Attendu"  
> **Date de vérification** : 08 Janvier 2026  
> **Données** : 1000 trajectoires, IC 95%

---

## Indicateur 1 : Démarche Itérative avec Métriques Prédéfinies

### Niveau visé : ✅ Dépasse les attentes

| Critère | Preuve | Fichier/Section |
|---------|--------|-----------------|
| **Contextualisation des métriques selon les acteurs** | Analyse des stakeholders avec métriques spécifiques (étudiants, administrateurs, infrastructure) | [02_analyse_stakeholders.md](02_analyse_stakeholders.md) |
| **Préconisations appuyées par simulations quantifiables** | 1000 trajectoires, IC 95%, comparaison théorie/simulation | [04_donnees_brutes.md](04_donnees_brutes.md), [01_rapport_analyse.md](01_rapport_analyse.md) |
| **Évolution qualifiable des métriques** | Étude paramétrique (λ, K, ks, kf), analyse de sensibilité | [03_recommandations.md](03_recommandations.md) Section 2 |
| **Prise en compte des risques** | Analyse des pages blanches, taux de rejet, scénarios de surcharge | [05_synthese_executive.md](05_synthese_executive.md) |

### Métriques Utilisées

| Métrique | Priorité | Justification |
|----------|----------|---------------|
| E[W] (Temps de séjour) | ⭐⭐⭐ | Impact direct sur UX étudiant |
| Taux de rejet | ⭐⭐⭐ | Frustration utilisateur |
| Taux de perte (pages blanches) | ⭐⭐⭐ | Fiabilité perçue |
| Variance/IC | ⭐⭐ | Prévisibilité du service |
| ρ (Utilisation) | ⭐⭐ | Indicateur de saturation |
| Équité ING/PREPA | ⭐ | Fairness entre populations |

---

## Indicateur 2 : Analyse des Limites et Recommandations

### Niveau visé : ✅ Dépasse les attentes

| Critère | Preuve | Fichier/Section |
|---------|--------|-----------------|
| **1. Périmètre de validité selon paramètres** | Conditions de stabilité (ρ₁<1, ρ₂<1), plages de λ valides | [01_rapport_analyse.md](01_rapport_analyse.md) Section 2, 5 |
| **2. Qualification du comportement vs théorie** | Comparaison M/M/K théorique vs simulé (erreur < 0.5%) | [04_donnees_brutes.md](04_donnees_brutes.md) Section 2.3 |
| **3. Consolidation par analyse statistique** | IC 95%, 1000 trajectoires, variance empirique | Scripts de simulation, [04_donnees_brutes.md](04_donnees_brutes.md) |

### Benchmark Versionné

| Version | Modification | Impact Mesuré |
|---------|--------------|---------------|
| v1.0 | Files infinies baseline | E[W] = 1.7195 ± 0.0090 |
| v1.1 | Files finies (ks=10, kf=5) | Rejet +0.89%, Perte +8.5% |
| v1.2 | Backup p=0.5 | Pages blanches -27% (19.5% → 14.3%) |
| v1.3 | Multi-populations | Ratio ING/PREPA = 1.10 |
| v1.4 | Priorités PREPA_FIRST | Ratio amélioré à 1.08 |

### Périmètre de Validité Identifié

```
STABLE si :
  - ρ₁ = λ/(K×μ₁) < 1
  - ρ₂ = λ/μ₂ < 1
  
RECOMMANDÉ si :
  - ρ₁ < 0.8 (marge 20%)
  - ρ₂ < 0.85 (marge 15%)
  
CRITIQUE si :
  - ρ > 0.9 → temps de séjour explosent
```

---

## Indicateur 3 : Facteurs Externes (Humains, Organisationnels)

### Niveau visé : ✅ Dépasse les attentes

| Critère | Preuve | Fichier/Section |
|---------|--------|-----------------|
| **Qualification de l'impact** | Analyse coût/bénéfice pour chaque acteur | [02_analyse_stakeholders.md](02_analyse_stakeholders.md) |
| **Test contre scénarios distincts** | Scénarios TP standard, Projet, Deadline, Pics de charge | [03_recommandations.md](03_recommandations.md) Section 2.1 |
| **Étude de terrain/interviews simulés** | Personas (Léo ING, Marie PREPA) avec comportements typiques | [02_analyse_stakeholders.md](02_analyse_stakeholders.md) Section 2 |

### Acteurs Identifiés et Enjeux

| Acteur | Métrique Clé | Enjeu Principal | Recommandation |
|--------|--------------|-----------------|----------------|
| **Étudiant ING** | E[W], disponibilité | Feedback rapide, itérations fréquentes | Capacité suffisante (ks≥20) |
| **Étudiant PREPA** | Équité, fiabilité | Pas de discrimination, résultats garantis | Politique PREPA_FIRST |
| **Admin Infrastructure** | ρ, coût serveurs | Optimisation ressources | Monitoring ρ₂, scaling |
| **Enseignant** | Fiabilité, deadline | Rendu des notes à temps | Backup systématique en deadline |

### Scénarios Utilisateurs Testés

| Scénario | λ | Comportement Observé | Recommandation |
|----------|---|----------------------|----------------|
| TP Standard | 2.0 | ✅ E[W] < 1 min | Config STANDARD |
| Projet Normal | 4.0 | ⚠️ Pertes 8.5% | Activer backup p=0.5 |
| Deadline | 8.0+ | ❌ Rejet > 25% | Config RENFORCÉE + throttling |

---

## Compétences Transversales

### Recherche Documentaire
- ✅ Références : Kendall (1953), Jackson (1957), Burke (1956)
- ✅ Modèles théoriques : M/M/K, réseaux de Jackson, formule Erlang C

### Discours Scientifique Rigoureux
- ✅ Notation Kendall pour les files d'attente
- ✅ Formules mathématiques avec LaTeX ($\rho$, $\lambda$, $\mu$)
- ✅ Intervalles de confiance avec justification statistique

### Traduction Problème → Formalisme
- ✅ Moulinette → Réseau de files en tandem
- ✅ Push tags → Processus de Poisson
- ✅ Exécution tests → Service exponentiel

### Sélection Solution sur Critères
- ✅ Comparaison quantitative des configurations
- ✅ Front de Pareto pour compromis multi-objectifs
- ✅ Optimisation avec `scipy.optimize`

---

## Checklist Finale

### Code
- [x] Simulateur files infinies validé vs théorie
- [x] Simulateur files finies avec rejets/pertes
- [x] Multi-populations avec superposition
- [x] Module d'optimisation paramètres
- [x] 1000 trajectoires pour IC robustes

### Rapports
- [x] Analyse complète avec hypothèses explicites
- [x] Données brutes avec IC 95%
- [x] Recommandations quantifiées
- [x] Synthèse exécutive pour décideurs
- [x] Analyse stakeholders multi-perspectives

### Présentation
- [x] Notebook interactif illustratif
- [x] Graphiques et tableaux clairs
- [x] Justification de tous les choix

---

## Résumé Conformité

| Indicateur | Niveau Actuel | Objectif | Statut |
|------------|---------------|----------|--------|
| 1. Démarche itérative | Dépasse les attentes | Attendu minimum | ✅ |
| 2. Analyse limites | Dépasse les attentes | Attendu minimum | ✅ |
| 3. Facteurs externes | Dépasse les attentes | Attendu minimum | ✅ |

**Conclusion** : Le projet répond aux critères "Dépasse les attentes" pour les trois indicateurs.

---

*Dernière vérification : Janvier 2026*
