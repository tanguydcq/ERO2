# 📊 Structure de la Soutenance - Projet ERO2 (Moulinette)

**Durée totale :** 15 minutes (2min30 par personne)
**Objectif :** Démontrer la démarche scientifique, la validation des hypothèses et la pertinence des recommandations (Niveau Expert).

---

## 👤 Orateur 1 : Cadre Théotique & Synthèse (Le "Fil Rouge")
*Rôle : Poser les bases mathématiques solides et conclure sur les actions concrètes.*

* [cite_start]**Le Système Modélisé :** Présenter la moulinette comme un **Réseau de Jackson en tandem** composé de deux stations[cite: 52].
    * [cite_start]Station 1 (Tests) : $M/M/K$ avec $K=3$ serveurs[cite: 52].
    * [cite_start]Station 2 (Affichage) : $M/M/1$ (un seul serveur)[cite: 52].
* **Hypothèses Mathématiques :**
    * [cite_start]Arrivées selon un **processus de Poisson** (indépendance des soumissions)[cite: 54].
    * [cite_start]**Théorème de Burke :** Crucial, il prouve que la sortie de la station 1 reste un processus de Poisson, permettant d'analyser les stations indépendamment[cite: 80, 83].
* **Validation du Simulateur :**
    * [cite_start]Comparaison Théorie vs Simulation : L'erreur sur les temps de séjour est inférieure à **0.16%**[cite: 100].
    * [cite_start]Vérification de la **Loi de Little** ($L = \lambda \times W$) : Écart constaté inférieur à 0.1%, validant la fiabilité de l'outil[cite: 391].
* **(À garder pour la fin de la présentation) Conclusion & Recommandations :**
    * [cite_start]**Priorité 1 :** Augmenter la capacité de retour ($k_f$) de 5 à 10 pour réduire les pertes de 60%[cite: 395].
    * [cite_start]**Priorité 2 :** Activer le backup aléatoire ($p=0.5$)[cite: 396].
    * [cite_start]**Priorité 3 :** Politique `PREPA_FIRST` pour gérer l'hétérogénéité[cite: 397].

---

## 👤 Orateur 2 : Simulation 1 - La Réalité des Capacités Finies
*Rôle : Montrer les limites physiques du système et le goulot d'étranglement.*

* **Le problème des files infinies :** Dans la réalité, le stockage est limité. [cite_start]Introduction des paramètres $k_s$ (file d'entrée) et $k_f$ (file de retour)[cite: 107].
* **Rejet vs Perte (Distinction critique) :**
    * [cite_start]**Rejet (File 1 pleine) :** L'étudiant reçoit une erreur immédiate, peut réessayer (frustration modérée)[cite: 109].
    * **Perte (File 2 pleine) :** Le calcul est fait mais le résultat est perdu ("Page blanche"). [cite_start]C'est le pire scénario utilisateur[cite: 112].
* **Analyse de la saturation (Table 2) :**
    * [cite_start]Avec une charge élevée ($\lambda=6$), près de **30%** des soumissions sont en échec (rejetées ou perdues)[cite: 119].
    * [cite_start]Le taux de perte ("pages blanches") se stabilise autour de **24%**[cite: 123].
* **Identification du Goulot :**
    * [cite_start]Le débit effectif plafonne à **4 jobs/min**[cite: 122].
    * [cite_start]C'est la capacité de la **Station 2** ($M/M/1$) qui limite tout le système, peu importe la puissance de calcul ajoutée en amont[cite: 122].

---

## 👤 Orateur 3 : Simulation 2 - Stratégies de Backup (Fiabilité)
*Rôle : Proposer une solution technique au problème des "pages blanches".*

* [cite_start]**Le concept de Backup :** Sauvegarder les résultats en tampon avant la file 2 pour éviter la perte sèche si la file est pleine[cite: 128].
* **Le dilemme Stockage vs Fiabilité :**
    * [cite_start]**Backup Systématique :** 0% de perte, mais coûte trop cher en stockage (8000 unités)[cite: 132, 140].
    * [cite_start]**Backup Aléatoire :** Lisser la charge pour éviter la congestion[cite: 188].
* **Recherche de l'optimum (Table 3 & Fig 1) :**
    * Comparaison des probabilités $p=0.25$, $p=0.5$, $p=0.75$.
    * [cite_start]**Le gagnant :** Une probabilité **$p=0.5$**[cite: 136].
* **Résultats de la solution :**
    * [cite_start]Réduction des pages blanches de **30%** par rapport à l'absence de backup[cite: 136].
    * [cite_start]Utilisation de moitié moins de stockage que le systématique[cite: 136].
    * [cite_start]Coût en temps de séjour négligeable (+0.23 min), ce qui rend la solution acceptable[cite: 137].

---

## 👤 Orateur 4 : Simulation 3 - Le Cas Multi-Populations (ING vs PREPA)
*Rôle : Analyser l'impact de comportements utilisateurs différents.*

* **Modélisation des profils :**
    * [cite_start]**ING :** Code optimisé, tests rapides ($\mu_1=4.0$)[cite: 193].
    * [cite_start]**PREPA :** Code moins mature, tests 4x plus longs ($\mu_1=1.0$)[cite: 197].
* [cite_start]**Principe de Superposition :** Rappel théorique que la somme de deux processus de Poisson indépendants reste un processus de Poisson (simplifie l'analyse globale)[cite: 200, 203].
* **Constat d'Inégalité (Table 4) :**
    * [cite_start]Les PREPA subissent un temps de séjour moyen de **3.11 min** contre **2.84 min** pour les ING[cite: 206].
    * [cite_start]Le ratio $P/I$ est de **1.10**, indiquant une pénalité structurelle de 10% pour les étudiants les moins expérimentés[cite: 206].
* **Impact de la mixité (Table 5) :**
    * [cite_start]Plus la proportion d'ING augmente, meilleure est la performance globale du système car ils libèrent les ressources rapidement[cite: 248].

---

## 👤 Orateur 5 : Simulation 4 - La Fausse Bonne Idée (Blocage Périodique)
*Rôle : Présenter une approche naïve de régulation et expliquer son échec.*

* [cite_start]**Mécanisme testé :** Bloquer l'accès périodiquement (Cycle : fermé $t_b$, ouvert $t_b/2$) pour réguler le flux[cite: 255].
* [cite_start]**Disponibilité réduite :** Le système n'est accessible que **33.3%** du temps[cite: 257].
* **Le Paradoxe de l'Équité (Table 6) :**
    * *Point positif :* L'équité devient quasi-parfaite. [cite_start]Le ratio $P/I$ tombe à **1.01** et l'indice de Gini s'améliore de **75%**[cite: 265].
    * [cite_start]*Explication :* L'attente forcée devant la "porte fermée" est la même pour tous, ce qui gomme l'avantage de vitesse des ING[cite: 266].
* **Pourquoi c'est un échec (Fig 3) :**
    * [cite_start]Le prix à payer est inacceptable : les temps de séjour explosent de plus de **900%**[cite: 267].
    * Conclusion : L'équité stricte ne doit pas se faire au détriment de l'utilisabilité (Transition vers les priorités).

---

## 👤 Orateur 6 : Simulation 5 - Politiques de Priorité & Stabilité
*Rôle : Comparer les algorithmes pour trouver le meilleur compromis Équité/Performance.*

* **Comparatif des 4 Politiques (Table 7) :**
    * [cite_start]**FCFS (Standard) :** Ratio d'iniquité de 1.77[cite: 319].
    * [cite_start]**SRPT (Plus court d'abord) :** Meilleur temps global (1.15 min) mais désastreux pour l'équité (Ratio 3.31), les Prépas sont sacrifiés[cite: 348].
    * [cite_start]**SEPARATE :** Solution équilibrée mais sous-optimale[cite: 352].
    * **PREPA_FIRST (Discrimination positive) :** La meilleure solution. [cite_start]Ratio d'équité de **1.08** (proche de 1) avec un temps global acceptable (1.57 min)[cite: 350].
* **Carte de Stabilité (Table 8) :**
    * [cite_start]Définition des zones : **Optimale** ($\lambda < 3$), **Marginale** ($4.0 - 4.5$), **Critique** ($> 4.5$)[cite: 357].
* **Analyse de sensibilité :**
    * [cite_start]Augmenter le nombre de serveurs $K$ au-delà de 3 n'apporte qu'un gain marginal car le goulot reste la station 2[cite: 362].
    * Cela confirme la recommandation finale de l'intro : il faut investir sur la Station 2.