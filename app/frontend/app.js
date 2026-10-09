// const API_URL = "http://localhost:8000";
const API_URL = window.location.origin;

async function checkDeployment() {
    try {
        const response = await fetch(`${API_URL}/api/status`);
        const data = await response.json();
        
        let totalResources = 0;
        let readyResources = 0;

        for (const [namespace, resources] of Object.entries(data)) {
            for (const [resId, details] of Object.entries(resources)) {
                totalResources++;
                const cardId = `${namespace}-${resId}`;
                const cardElement = document.getElementById(cardId);
                
                if (cardElement) {
                    if (details.ready) {
                        cardElement.classList.remove('status-red');
                        cardElement.classList.add('status-green');
                        readyResources++;
                    } else {
                        cardElement.classList.remove('status-green');
                        cardElement.classList.add('status-red');
                    }
                }
            }
        }

        const percentage = Math.round((readyResources / totalResources) * 100);
        document.getElementById('progress-text').innerText = `${percentage}%`;

    } catch (error) {
        console.error("Erreur lors de la vérification du déploiement :", error);
        alert("Impossible de joindre l'API backend.");
    }
}

async function openModal(namespace, resourceId) {
    try {
        const response = await fetch(`${API_URL}/api/resources/${namespace}/${resourceId}`);
        const data = await response.json();

        document.getElementById('modal-title').innerText = data.name;
        document.getElementById('modal-name').innerText = data.name;
        document.getElementById('modal-ns').innerText = data.namespace;
        document.getElementById('modal-desc').innerText = data.description;
        document.getElementById('modal-instructions').innerText = data.instructions;
        document.getElementById('modal-label').innerText = data.label;
        document.getElementById('modal-kind').innerText = data.kind;
        document.getElementById('modal-port').innerText = data.port;
        document.getElementById('modal-dep').innerText = data.dep;

        document.getElementById('modal').style.display = "block";
    } catch (error) {
        console.error("Erreur lors de la récupération des détails :", error);
    }
}

function closeModal() {
    document.getElementById('modal').style.display = "none";
}

window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}