Voici une version structurée et formatée en Markdown du document, optimisée pour l'analyse par un agent IA.

# Projet ERO2 : La Moulinette comme Système d'Attente

## 1. Contexte et Objectifs

Ce projet propose d'analyser l'infrastructure de correction automatique de l'école, nommée "la moulinette", sous l'angle des systèmes d'attente. Bien que les éléments soient une simplification de la réalité, les questionnements relèvent de considérations réelles de développement.

* 
**Définition :** Une moulinette est une infrastructure logicielle exécutant des tests unitaires sur un code fourni par un tiers pour vérifier sa conformité fonctionnelle et technique.


* 
**Format :** Travail de groupe (4 à 6 étudiants), évalué par soutenance avec une grille critériée.


* 
**Approche :** Le sujet est descriptif et demande de proposer une modélisation du contexte en explicitant les hypothèses.



---

## 2. Livrables Attendus

Pour chaque scénario proposé, les éléments suivants doivent être fournis :

1. 
**Code de simulation :** Le code permettant de simuler les systèmes d'attente.


2. **Analyse comportementale :**
* Identification des paramètres en jeu.


* Analyse du comportement et de la stabilité du système en fonction de ces paramètres.


* Évaluation via des métriques standard : nombre d'agents, temps de séjour, taux de blocage, etc..


* Synthèse et recommandations pour des plages de paramètres acceptables, incluant une analyse des risques utilisateur.




3. 
**Résultats bruts :** Données de simulations soutenant les observations.



> **Note importante :** Les arguments doivent être étayés par des éléments factuels et statistiques (benchmarking). Un résultat unique ne suffit pas.
> 
> 

---

## 3. Terminologie et Concepts

### 3.1 L'Utilisateur

Un utilisateur est une personne accédant à l'infrastructure pour une activité pédagogique. Il effectue deux actions :

* 
**Push standard :** Versionnage du code (git).


* 
**Push tag :** Déclenche l'exécution des tests unitaires pour obtenir un retour.



### 3.2 La Moulinette

Elle est constituée formellement de:

* 
**Une test-suite :** Ensemble de tests unitaires (complet ou partiel).


* 
**Un niveau d'information de retour :** Erreur précise, aide spécifique ou simple rejet.


* 
**Des ressources :** Quotas de "push tags" (total, par heure, par plage horaire).



### 3.3 Workflow Nominal

1. L'étudiant travaille sur son dépôt git (commits/pushs standards).


2. L'utilisation d'un **tag réservé** déclenche la vérification.


3. La test-suite est exécutée selon un schéma de système d'attente (immédiat ou mise en file).


4. Le résultat est affiché selon le niveau d'information défini par le concepteur.



---

## 4. Études de Cas

Les cas sont présentés par ordre croissant de complexité.

4.1 Modèle "Waterfall" 

Ce modèle suit un processus séquentiel.

#### Scénario 1 : Files infinies

* **Processus :**
1. **Entrée :** Un push tag place le code dans une file FIFO infinie.  serveurs sont disponibles pour l'exécution.


2. 
**Sortie :** Le résultat est placé dans une file FIFO infinie gérée par un serveur unique pour l'envoi vers le front.




* 
**Travail demandé :** Proposer un système d'attente modélisant ce contexte et simuler son comportement selon les paramètres.



#### Scénario 2 : Files finies

L'hypothèse des files infinies est levée face à l'augmentation du nombre d'étudiants.

* 
**Paramètres :**  (taille file exécution) et  (taille file résultats).


* **Règles de rejet :**
* Si push tag refusé : Message d'erreur.


* Si résultat refusé (file résultats pleine) : Retour vide (page blanche) à l'étudiant.




* 
**Travail demandé :** Discuter des proportions de refus selon les paramètres.



#### Scénario 3 : Back-up des résultats

Mise en place d'un back-up en amont de la seconde file pour éviter la perte de données.

* **Travail demandé :**
* Analyser l'impact sur la proportion de pages blanches.


* Identifier les nouveaux problèmes potentiels.


* Discuter : Back-up aléatoire vs systématique.


* Calculer le temps de séjour moyen et la variance empirique.





4.2 Modèle "Channels and Dams" 

Ce modèle introduit des distinctions entre populations d'étudiants.

#### Contexte

* 
**Population ING (Atelier C) :** Arrivées fréquentes.


* 
**Population PREPA :** Rendus plus rares mais occupant la moulinette plus longtemps.


* 
**Observation :** Temps d'attente inégaux.



#### Travail demandé

1. 
**Simulation :** Simuler les variations de temps de séjour décrites pour ces populations.


2. **Régulation :**
* Mécanisme : Blocage de la moulinette pour un temps , puis ouverture pour , de manière cyclique, pour réguler la population ING.


* Comparaison : Comparer ce modèle avec le précédent (Waterfall) en termes de temps de séjour.


* Optimisation : Proposer un autre système d'attente minimisant le temps de séjour moyen pour les deux populations.