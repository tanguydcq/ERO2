---
applyTo: "**"
---

# Scénarios Techniques à Simuler

L’étude des modèles de "moulinettage" implique des choix dépendants du contexte. Vous devez analyser et simuler les cas suivants, présentés par ordre croissant de complexité.

Pour chaque cas, vous devez fournir le code de simulation et une analyse comportementale.

## Étude de Cas 1 : "Waterfall"

Dans ce modèle, tout agent de la population suit le processus suivant :

1.  **File d'exécution** : Un _push tag_ place le code dans une file d’attente FIFO infinie. Un nombre $K$ de serveurs est disponible pour exécuter la test-suite.
2.  **File de retour** : Une fois exécuté, le résultat est placé dans une seconde file d’attente FIFO infinie, gérée par un **serveur unique**, pour l’envoi vers le front (affichage étudiant).

### Tâches à réaliser :

1.  **Modélisation de base** : Proposez un système d’attente modélisant ce contexte. Effectuez des simulations pour analyser son comportement selon les paramètres en jeu.
2.  **Files Finies** : Avec l'augmentation du nombre d'étudiants, l'hypothèse de files infinies est rejetée.
    - Soit $k_s$ la taille de la file d'exécution.
    - Soit $k_f$ la taille de la file de renvoi de résultats.
    - _Règle_ : Si un push tag est refusé (file pleine), l'étudiant reçoit une erreur. Si un résultat est refusé dans la seconde file, l'étudiant reçoit un retour vide.
    - **Analyse demandée** : Discutez des proportions de refus selon les paramètres.
3.  **Back-up** : Pour éviter la perte de données (pages blanches), un back-up des résultats est mis en place en amont de la seconde file.
    - **Analyse demandée** :
      - Quel changement cela opère-t-il sur la proportion de pages blanches ?
      - Quels problèmes peuvent surgir avec cette solution ?
      - Discutez des avantages d’un back-up aléatoire plutôt que systématique.
      - Calculez le temps de séjour moyen et la variance empirique dans ce modèle.

## Étude de Cas 2 : "Channels and dams"

On observe que certaines populations ont des comportements différents.

- **Population ING (Atelier C)** : Arrivées fréquentes.
- **Population PREPA** : Rendus plus rares, mais occupent la moulinette plus longtemps (temps de traitement plus long).

### Tâches à réaliser :

1.  **Simulation hétérogène** : Simulez les variations de temps de séjour par population décrites ci-dessus.
2.  **Régulation (Throttling)** : Pour réguler la population ING, un blocage de la moulinette est introduit pour un temps $t_b$, puis ouvert pour $t_b / 2$, etc.
    - **Analyse demandée** : Comparez ce modèle avec le précédent en termes de temps de séjour.
    - **Proposition** : Proposez un _autre_ système d’attente pour minimiser le temps de séjour moyen pour les deux populations simultanément.
