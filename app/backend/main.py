from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
import os

app = FastAPI(title="Kubernetes TP Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du client Kubernetes
try:
    config.load_incluster_config()
except ConfigException:
    try:
        config.load_kube_config()
    except Exception:
        print("Avertissement : Impossible de charger la configuration Kubernetes. Les checks renverront False.")

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
networking_v1 = client.NetworkingV1Api()

def check_resource_exists(namespace: str, kind: str, name: str) -> bool:
    try:
        if kind == "pod":
            pods = v1.list_namespaced_pod(namespace=namespace)
            return len(pods.items) > 0
        elif kind == "configmap":
            v1.read_namespaced_config_map(name=name, namespace=namespace)
            return True
        elif kind == "service":
            v1.read_namespaced_service(name=name, namespace=namespace)
            return True
        elif kind == "deployment":
            apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return True
        elif kind == "secret":
            v1.read_namespaced_secret(name=name, namespace=namespace)
            return True
        elif kind == "pvc":
            v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
            return True
        elif kind == "pv":
            v1.read_persistent_volume(name=name)
            return True
        elif kind == "netpol":
            networking_v1.read_namespaced_network_policy(name=name, namespace=namespace)
            return True
    except ApiException as e:
        # 404 signifie que la ressource n'existe pas encore sur le cluster (comportement normal)
        if e.status == 404:
            return False
        print(f"Erreur API K8s pour {namespace}/{kind}/{name}: {e.status}")
        return False
    except Exception as e:
        print(f"Erreur inattendue pour {namespace}/{kind}/{name}: {e}")
        return False
    return False

# Base de connaissances pédagogique pour chaque ressource cliquable
resources_knowledge = {
    "front-ns.page-web": {
        "name": "library-frontend (Front-end)",
        "namespace": "front-ns",
        "kind": "deployment",
        "label": "app=front",
        "port": "80",
        "dep": "front-config (ConfigMap) & nginx-config (ConfigMap Reverse Proxy)",
        "description": "Contient l'application statique (HTML/CSS/JS) pour gérer la bibliothèque de livres.",
        "instructions": "Déployer sous forme de Deployment dans le namespace front-ns."
    },
    "front-ns.configmap": {
        "name": "front-config (ConfigMap)",
        "namespace": "front-ns",
        "kind": "configmap",
        "label": "app=front",
        "port": "N/A",
        "dep": "Aucune",
        "description": "Fournit la configuration spécifique (ex. URL de l'API backend) au front-end.",
        "instructions": "Créer une ConfigMap contenant la page index.html et la monter au niveau du /usr/share/nginx/html."
    },
    "front-ns.nginx-config": {
        "name": "nginx-config (ConfigMap Reverse Proxy)",
        "namespace": "front-ns",
        "kind": "configmap",
        "label": "app=front",
        "port": "N/A",
        "dep": "library-backend-svc (Service)",
        "description": "Configuration Nginx (default.conf) pour servir le front et proxifier la route /api/ vers le service backend.",
        "instructions": "Créer une ConfigMap contenant le fichier default.conf de Nginx et le monter au niveau du /etc/nginx/conf.d/default.conf."
    },
    "front-ns.service": {
        "name": "library-frontend-svc (Service)",
        "namespace": "front-ns",
        "kind": "service",
        "label": "app=front",
        "port": "80:30080/TCP",
        "dep": "library-frontend (Deployment)",
        "description": "Expose l'application front-end à l'extérieur du cluster sur un port fixe.",
        "instructions": "Créer un service de type NodePort avec un nodePort fixe (ex: 30080)."
    },
    "back-ns.back-end": {
        "name": "library-backend (Back-end Python)",
        "namespace": "back-ns",
        "kind": "deployment",
        "label": "app=backend",
        "port": "8000",
        "dep": "backend-config (ConfigMap), postgres-secret (Secret), regcred (ImagePullSecret), postgres (Service)",
        "description": "API REST gérant la logique métier et les requêtes vers PostgreSQL.",
        "instructions": "Déployer l'application FastAPI en s'assurant d'injecter les variables d'environnement et l'imagePullSecrets."
    },
    "back-ns.regcred": {
        "name": "regcred (ImagePullSecret)",
        "namespace": "back-ns",
        "kind": "secret",
        "label": "type=kubernetes.io/dockerconfigjson",
        "port": "N/A",
        "dep": "Registre d'images privé (Docker Hub / Registry)",
        "description": "Secret d'authentification Docker utilisé par K8s via imagePullSecrets pour télécharger l'image privée du backend.",
        "instructions": "Créer un secret de type docker-registry avec `kubectl create secret docker-registry regcred ...`."
    },
    "back-ns.postgresql": {
        "name": "postgres-db (PostgreSQL)",
        "namespace": "back-ns",
        "kind": "deployment",
        "label": "app=postgres",
        "port": "5432",
        "dep": "postgres-secret (Secret), postgres-pvc (PVC)",
        "description": "Base de données relationnelle pour stocker les livres de la bibliothèque.",
        "instructions": "Déployer PostgreSQL en consommant les secrets via envFrom et le PVC pour la persistance."
    },
    "back-ns.secret": {
        "name": "postgres-secret (Secret)",
        "namespace": "back-ns",
        "kind": "secret",
        "label": "app=postgres",
        "port": "N/A",
        "dep": "Aucune",
        "description": "Contient les identifiants sensibles (utilisateur et mot de passe) de la base de données.",
        "instructions": "Créer un Secret Kubernetes pour la BDD."
    },
    "back-ns.pv": {
        "name": "postgres-pv (PersistentVolume)",
        "namespace": "back-ns",
        "kind": "pv",
        "label": "type=local",
        "port": "N/A",
        "dep": "Dossier hôte local (/data/postgres)",
        "description": "Volume de stockage physique lié au host (hostPath) pour la persistance.",
        "instructions": "Définir un PersistentVolume avec un accès ReadWriteOnce pointant vers un dossier de l'hôte."
    },
    "back-ns.pvc": {
        "name": "postgres-pvc (PersistentVolumeClaim)",
        "namespace": "back-ns",
        "kind": "pvc",
        "label": "app=postgres",
        "port": "N/A",
        "dep": "postgres-pv (PV)",
        "description": "Requête de réservation de volume persistant pour PostgreSQL.",
        "instructions": "Lier le PVC au PV créé précédemment pour allouer le stockage au Deployment."
    },
    "back-ns.netpol": {
        "name": "db-isolation (NetworkPolicy)",
        "namespace": "back-ns",
        "kind": "netpol",
        "label": "app=postgres",
        "port": "5432/TCP",
        "dep": "library-backend (Pods avec label app=backend)",
        "description": "Sécurise la base de données en autorisant l'ingress uniquement depuis le pod backend.",
        "instructions": "Créer une NetworkPolicy restrictive ciblant les labels du pod PostgreSQL."
    }
}

@app.get("/api/status")
async def get_status():
    return {
        "front-ns": {
            "page-web": {"ready": check_resource_exists("front-ns", "deployment", "library-frontend"), "name": "Page Web (Front-end)"},
            "configmap": {"ready": check_resource_exists("front-ns", "configmap", "front-config"), "name": "ConfigMap (Config)"},
            "nginx-config": {"ready": check_resource_exists("front-ns", "configmap", "nginx-config"), "name": "nginx-config"},
            "service": {"ready": check_resource_exists("front-ns", "service", "library-frontend-svc"), "name": "Service NodePort"}
        },
        "back-ns": {
            "back-end": {"ready": check_resource_exists("back-ns", "deployment", "library-backend"), "name": "Back-end (Python)"},
            "regcred": {"ready": check_resource_exists("back-ns", "secret", "regcred"), "name": "Secret Registre (regcred)"},
            "postgresql": {"ready": check_resource_exists("back-ns", "deployment", "postgres-db"), "name": "PostgreSQL"},
            "secret": {"ready": check_resource_exists("back-ns", "secret", "postgres-secret"), "name": "Secret BDD"},
            "pv": {"ready": check_resource_exists("back-ns", "pv", "postgres-pv"), "name": "PersistentVolume (PV)"},
            "pvc": {"ready": check_resource_exists("back-ns", "pvc", "postgres-pvc"), "name": "PersistentVolumeClaim (PVC)"},
            "netpol": {"ready": check_resource_exists("back-ns", "netpol", "db-isolation"), "name": "NetworkPolicy"}
        }
    }

@app.get("/api/resources/{namespace}/{resource_id}")
async def get_resource_details(namespace: str, resource_id: str):
    key = f"{namespace}.{resource_id}"
    if key not in resources_knowledge:
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    return resources_knowledge[key]

# Monter le dossier frontend pour servir l'interface web sur la racine "/"
app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")