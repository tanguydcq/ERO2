# Notes de Coaching - Réunion du 16/12/2025

> **Synthèse des conseils reçus lors de la réunion avec le coach**  
> Participants : Tanguy, Quentin Gillet  
> Objectif : Améliorer l'analyse et la présentation du projet ERO2

---

## 📋 Résumé des Conseils Clés

### 1. Méthodologie de Simulation

| Conseil | Explication | Statut Actuel |
|---------|-------------|---------------|
| **1000 trajectoires** | Simuler au minimum 1000 trajectoires pour obtenir des estimations fiables | ⚠️ À vérifier/augmenter |
| **Régime stationnaire** | Analyser la moyenne en régime stationnaire (après warm-up) | ✅ Implémenté (warmup_jobs) |
| **Variance empirique** | Calculer les variances pour avoir des intervalles de confiance valides | ✅ Implémenté |
| **Intervalles de confiance** | Présenter les IC à 95% pour toutes les métriques | ⚠️ À renforcer |

### 2. Modélisation "Channels and Dams"

**Principe de Superposition des Processus de Poisson :**

$$N_1 + N_2 \sim \text{PPH}(\lambda_{\text{ing}} + \lambda_{\text{prepa}})$$

- Les arrivées des ingénieurs ($\lambda_{\text{ing}}$) et des prépa ($\lambda_{\text{prepa}}$) sont des processus de Poisson indépendants
- La **superposition** de deux processus de Poisson est aussi un processus de Poisson
- Taux total : $\lambda_{\text{total}} = \lambda_{\text{ing}} + \lambda_{\text{prepa}}$
- **Action** : Expliciter ce principe dans l'analyse théorique

### 3. Métriques à Présenter

Les métriques suivantes doivent être analysées et présentées avec graphiques :

| Métrique | Symbole | Description |
|----------|---------|-------------|
| Coûts | $C$ | Coût d'infrastructure (serveurs, stockage) |
| Temps total | $E[W]$ | Temps de séjour moyen |
| Taux de rejet | $P_{reject}$ | Proportion de push tags refusés |
| Espérance | $\mu$ | Moyenne empirique des métriques |
| Variance | $\sigma^2$ | Variance empirique pour IC |

### 4. Optimisation et Paramètres Optimaux

**Utilisation de l'optimisation de fonction (OCON/scipy.optimize) :**

```python
from scipy.optimize import minimize

def cost_function(params, constraints):
    """Fonction objectif à minimiser."""
    # Ex: minimiser temps_moyen + coût_rejet * taux_rejet
    return weighted_metric(params)
    
# Trouver les paramètres optimaux
optimal_params = minimize(cost_function, x0, constraints=constraints)
```

**Objectif** : Trouver les paramètres (K, ks, kf, λ) qui optimisent le compromis temps/coût/rejet.

### 5. Présentation des Résultats

- [x] **Graphiques** : Visualisations claires des comportements
- [x] **Tableaux** : Résultats numériques avec IC
- [ ] **Notebook illustratif** : Jupyter interactif pour démonstrations
- [ ] **Site interactif** : Interface pour explorer les paramètres (optionnel)

---

## 📌 Actions à Réaliser

### Court Terme (Prioritaire)

1. **Augmenter le nombre de trajectoires** : Passer à 1000 simulations minimum
2. **Expliciter le principe de superposition** : Ajouter section théorique
3. **Notebook Jupyter illustratif** : Créer un notebook interactif
4. **Double file justifiée** : Si modèle différent, justifier le choix

### Moyen Terme

5. **Optimisation des paramètres** : Implémenter une recherche de paramètres optimaux
6. **Analyse comparative** : Comparer plusieurs scénarios systématiquement
7. **Justification des choix** : Documenter TOUS les choix de modélisation

### Long Terme (Bonus)

8. **Interface interactive** : Tableau de bord ou application web
9. **Contact administrateurs** : Valider les hypothèses avec données réelles (si possible)

---

## 🎯 Points de Notation Importants

> **Citation Tanguy** : "Faut tout expliquer dans nos choix → c'est là qu'on sera noté"

### Critères d'Excellence (Grille d'Évaluation)

1. **Démarche itérative** : Montrer l'évolution des analyses
2. **Métriques contextualisées** : Adapter aux différents stakeholders
3. **Préconisations quantifiées** : Appuyer par des simulations variées
4. **Risques identifiés** : Analyser les cas limites et pathologiques

---

## 📊 Checklist de Validation

### Simulation
- [ ] 1000+ trajectoires par scénario
- [ ] Warm-up suffisant (vérifier convergence)
- [ ] Variance et IC calculés
- [ ] Seed fixé pour reproductibilité

### Modélisation
- [ ] Hypothèses explicites (Poisson, exponentielles)
- [ ] Principe de superposition expliqué
- [ ] Choix de discipline (FIFO, priorité) justifié
- [ ] Limites du modèle discutées

### Présentation
- [ ] Graphiques temps de séjour vs λ
- [ ] Graphiques taux de rejet vs capacité
- [ ] Tableaux comparatifs des scénarios
- [ ] Intervalles de confiance affichés

### Optimisation
- [ ] Fonction objectif définie
- [ ] Contraintes identifiées
- [ ] Paramètres optimaux trouvés
- [ ] Sensibilité analysée

---

## 💡 Interprétation des Notes Brutes

| Note Originale | Interprétation |
|----------------|----------------|
| "trajectoire" | Simuler plusieurs trajectoires (réplications) |
| "contexte" | Bien situer le problème (moulinette EPITA) |
| "optimize python" | Utiliser scipy.optimize pour trouver paramètres optimaux |
| "couts" | Intégrer une notion de coût dans l'analyse |
| "PPH" | Processus de Poisson Homogène |
| "double file" | Modèle en tandem (2 stations) - si non utilisé, justifier |
| "ocon" | Probablement scipy.optimize ou optimisation |
| "notebook illustratif" | Créer un Jupyter interactif |
| "site interactif" | Dashboard ou app web (bonus) |

---

## 📁 Fichiers à Créer/Modifier

1. `notebooks/demo_interactive.ipynb` - Notebook Jupyter illustratif
2. `optimization/parameter_optimization.py` - Recherche paramètres optimaux
3. `reports/01_rapport_analyse.md` - Ajouter section superposition
4. Scripts de simulation - Augmenter n_trajectories à 1000+

