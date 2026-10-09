# 🚀 TP Kubernetes — Déploiement d'une Application 3-Tiers & Audit Dynamique

Bienvenue dans ce TP pratique ! L'objectif est de déployer une application web complète (Architecture 3-Tier : Frontend Nginx, Backend API Python/FastAPI, et Base de données PostgreSQL) découpée sur deux namespaces distincts (`front-ns` et `back-ns`).

Un **Dashboard d'audit en temps réel** est déployé au démarrage pour vous permettre de suivre votre progression et de valider la conformité de vos ressources sur le cluster.

---

## 📋 Prérequis (Requirements)

Avant de commencer, assurez-vous de disposer des éléments suivants sur votre poste de travail :

1. **Un cluster Kubernetes local ou distant** fonctionnel :
   * [Minikube](https://minikube.sigs.k8s.io/)
   * [k3s](https://k3s.io/) / [k3d](https://k3d.io/)
   * [Kind](https://kind.sigs.k8s.io/)
2. **`kubectl`** installé et configuré pour pointer vers votre cluster.
3. **Un compte Docker Hub** (ou un registre privé d'images de conteneurs) ainsi qu'un Personal Access Token (PAT) ou mot de passe.
4. **Docker / Podman** installé localement pour builder et pusher vos images personnalisées.

---

## 🎬 Démarrage du TP

Pour initialiser l'environnement de TP et déployer le dashboard d'audit interactif, exécutez la commande suivante à la racine du projet :

```bash
kubectl apply -f manifests/deploy.yaml
```

Une fois le dashboard déployé, accédez à l'interface web (via le service NodePort ou un kubectl port-forward) pour visualiser le schéma dynamique de l'architecture et suivre votre score d'avancement

## 🎮 Règles du Jeu & Objectifs du TP

Votre objectif est de faire passer l'indicateur d'avancement du Dashboard de **0% à 100%** en créant et déployant l'ensemble des objets Kubernetes requis dans les namespaces `front-ns` et `back-ns`.

### 1. Organisation des Namespaces
L'application doit être strictement isolée sur deux namespaces :
* **`front-ns`** : Héberge la couche de présentation.
* **`back-ns`** : Héberge la couche API, la base de données, la persistance et les secrets.

---

### 2. Liste des Ressources à Déployer

Le dashboard vérifie la présence et la conformité des ressources suivantes :

#### 🔹 Namespace `front-ns`
1. **ConfigMap (`front-config`)** : Contient la configuration du frontend (ex: URL d'accès au backend API).
2. **Deployment (`library-frontend`)** : Déploie l'application frontend statique (Nginx).
3. **Service NodePort (`library-frontend-svc`)** : Expose le frontend sur un port fixe du nœud (ex: `30080`).

#### 🔹 Namespace `back-ns`
4. **ImagePullSecret (`regcred`)** : Secret de type `docker-registry` contenant vos identifiants Docker Hub pour autoriser le cluster à télécharger votre image backend privée :
   ```bash
   kubectl create secret docker-registry regcred \
     --docker-server=[https://index.docker.io/v1/](https://index.docker.io/v1/) \
     --docker-username=<VOTRE_IDENTIFIANT_DOCKERHUB> \
     --docker-password=<VOTRE_TOKEN_DOCKERHUB> \
     --namespace=back-ns
    ````

5. **Deployment (`library-backend`)** : Variables de configuration non sensibles pour l'API Python (hôtes DB, ports).
6. **Secret BDD (`postgres-secret`)** : Stocke les identifiants sensibles de la base de données (POSTGRES_USER, POSTGRES_PASSWORD).
7. **PersistentVolume (`postgres-pv`)** : Allocation de stockage physique local (hostPath).
8. **PersistentVolumeClaim (`postgres-pvc`)** : Réservation du volume pour la base de données.
9. **Deployment (`postgres-db`)** : Déploiement du conteneur PostgreSQL consommant le secret BDD et le PVC.
10. **Deployment (`library-backend`)** : Déploiement de l'API REST FastAPI qui consomme backend-config, postgres-secret et utilise regcred dans imagePullSecrets.
11. **NetworkPolicy (`db-isolation`)** : Sécurise PostgreSQL en restreignant les flux d'entrée (ingress) uniquement aux Pods portant le label app=backend.

## 🔍 Suivi de l'Avancement

* **Visualisation sur le Dashboard :**
  * 🔴 **Pastille Rouge** : La ressource n'est pas détectée ou présente une dépendance manquante/erronée.
  * 🟢 **Pastille Verte** : La ressource est correctement déployée et validée par le cluster.
* **Informations ciblées :** En cliquant sur chaque ressource dans le schéma du dashboard, vous afficherez sa **Fiche Technique** (Kind, Ports, Labels selectors, Dépendances requises et consignes).

---

## 🛠️ Commandes Utiles pour le Débogage

Vérifier l'état de vos ressources en ligne de commande :

```bash
# Vérifier les ressources du frontend
kubectl get all -n front-ns

# Vérifier les ressources du backend
kubectl get all,pvc,secret,netpol -n back-ns

# Inspecter les logs d'un conteneur
kubectl logs -l app=backend -n back-ns

# Vérifier le binding du PVC
kubectl get pvc -n back-ns
```