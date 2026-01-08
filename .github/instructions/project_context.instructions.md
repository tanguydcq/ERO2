---
applyTo: "**"
---

# Contexte du Projet ERO2 : Analyse des Systèmes d'Attente

## 1. Description Générale

Ce projet s'inscrit dans le cadre de l'évaluation par compétences de l'École (EPITA). L'objectif est d'effectuer une analyse de l'infrastructure de correction automatique de l'école, appelée "la moulinette", sous l'angle des **systèmes d'attente (Queueing Theory)**.

Les éléments présentés ici constituent une simplification de la réalité, mais reposent sur des problématiques réelles de développement et d'infrastructure.

## 2. Parti Pris Pédagogique

Dans la démarche proposée, on cherche à analyser le comportement d'un système d'attente par deux perspectives complémentaires :

1. **La compréhension des modèles théoriques simples.**
2. **La simulation maîtrisée de systèmes plus complexes.**

Ces deux perspectives sont reliées :

- Nécessité d'aborder la théorie pour réaliser la simulation des composants.
- Utilité de la simulation pour l'étude des comportements pathologiques de tous les modèles (y compris simples).

## 3. Terminologie et Définitions

### Qu’est-ce qu’un utilisateur ?

Un utilisateur est une personne ayant accès à l’infrastructure de correction. Il peut effectuer deux actions :

- **Push code** : Pousser son code sur l’infrastructure (versionnage standard).
- **Push tag** : Pousser un tag sur un commit pour déclencher l’exécution des _test-suites_ et obtenir un retour sur la conformité (notation).

### Qu’est-ce qu’une moulinette ?

Une moulinette est constituée formellement de :

- **Une test-suite** : Ensemble de tests unitaires (éventuellement stratifiés).
- **Un niveau d’information de retour** : Message d'erreur précis, aide spécifique ou simple rejet.
- **Des ressources** : Quotas de _push tags_ (total, par heure, ou par plage horaire).

Le concepteur de l'activité définit ces paramètres et l'action du système lorsque les quotas sont atteints.

### Workflow Nominal

1.  L'étudiant code dans un repository git dédié.
2.  Il effectue des commits/push (sans tags) librement.
3.  Lorsqu'un **tag réservé** est utilisé, une vérification est faite.
4.  Si valide, la test-suite est exécutée selon le schéma du système d'attente (exécution immédiate, mise en file, etc.).
5.  Le résultat est affiché à l'étudiant selon le niveau d'information configuré.

**Enjeu de l'analyse :** Les choix d'architecture (système d'attente) par rapport aux contraintes imposées sont le cœur du projet.
