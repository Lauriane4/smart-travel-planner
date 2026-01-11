// 1. Gestion du changement de mode (Onglets)
function switchMode(mode) {
    const listContainer = document.getElementById('container-list');
    const textContainer = document.getElementById('container-text');
    const btnList = document.getElementById('btn-mode-list');
    const btnText = document.getElementById('btn-mode-text');
    
    if (mode === 'list') {
        listContainer.style.display = 'block';
        textContainer.style.display = 'none';
        btnList.classList.add('active');
        btnText.classList.remove('active');
    } else {
        listContainer.style.display = 'none';
        textContainer.style.display = 'block';
        btnText.classList.add('active');
        btnList.classList.remove('active');
    }
}

// 2. Fonction pour ajouter dynamiquement des lignes d'activités
function addActivityField() {
    const container = document.getElementById('activities-list');
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
        <input type="text" placeholder="Nom" class="act-name" title="Nom de l'activité">
        <input type="text" placeholder="Adresse" class="act-addr" title="Adresse de l'activité">
        <select class="act-cat" title="Catégorie">
            <option value="Musée">Musée</option>
            <option value="Parc">Parc</option>
            <option value="Restaurant">Restaurant</option>
            <option value="Monument">Monument</option>
            <option value="Shopping">Shopping</option>
            <option value="Boite de nuit">Boite de nuit</option>
            <option value="Autre">Autre</option>
        </select>
    `;
    container.appendChild(div);
}

// 3. Fonction pour envoyer les données au backend 
async function sendData() {
    const days = document.getElementById('days').value;
    const isTextMode = document.getElementById('container-text').style.display === 'block';
    let activities = [];

    if (isTextMode) {
        // --- LOGIQUE MODE TEXTE ---
        const bulkText = document.getElementById('bulk-text').value;
        const lines = bulkText.split('\n');
        lines.forEach(line => {
            if (line.includes(':')) {
                // 1. Séparer le nom et le reste (adresse + catégorie)
                const [name, rest] = line.split(':');
                
                let address = rest.trim();
                let category = "Autre"; // Valeur par défaut

                // 2. Chercher si une catégorie est entre parenthèses à la fin
                const catMatch = address.match(/\(([^)]+)\)$/);
                if (catMatch) {
                    category = catMatch[1]; // On récupère ce qu'il y a dans les parenthèses
                    address = address.replace(catMatch[0], "").trim(); // On l'enlève de l'adresse
                }

                if (name && address) {
                    activities.push({
                        name: name.trim(),
                        address: address,
                        category: category
                    });
                }
            }
        });
    } else {
        // --- LOGIQUE MODE LISTE ---
        const names = document.querySelectorAll('.act-name');
        const addresses = document.querySelectorAll('.act-addr');
        const categories = document.querySelectorAll('.act-cat');

        for (let i = 0; i < names.length; i++) {
            if (names[i].value && addresses[i].value) {
                activities.push({
                    name: names[i].value, 
                    address: addresses[i].value,
                    category: categories[i].value
                });
            }
        }
    }

    if (activities.length === 0) {
        alert("Ajoutez des activités (Format Nom : Adresse en mode texte) !");
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/optimize', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                days: parseInt(days), 
                activities: activities
            })
        });
        const result = await response.json();
        displayResult(result);
    } catch (error) {
        alert("Erreur de connexion au backend. Vérifie que Docker tourne !");
    }
}

// 4. Fonction d'affichage des résultats
function displayResult(data) {
    try {
        let html = "<h2>📅 Votre itinéraire optimisé :</h2>";
        for (const [day, dayActivities] of Object.entries(data)) {
            html += `<div class="day-card"><strong>${day}</strong><ul>`;
            dayActivities.forEach(act => {
                html += `<li><strong>${act.name}</strong> (${act.category}) - ${act.address}</li>`;
            });
            html += `</ul></div>`;
        }
        document.getElementById('result').innerHTML = html;
    } catch (e) {
        console.error("Erreur d'affichage :", e);
        document.getElementById('result').innerHTML = "<p style='color:red;'>Erreur lors de l'affichage.</p>";
    }
}