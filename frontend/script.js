// Fonction pour ajouter dynamiquement des lignes d'activités
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

        // Fonction pour envoyer les données au backend
        async function sendData() {
            const days = document.getElementById('days').value;
            const names = document.querySelectorAll('.act-name');
            const addresses = document.querySelectorAll('.act-addr');
            const categories = document.querySelectorAll('.act-cat');

            let activities = [];
            for(let i=0; i<names.length; i++) {
                if(names[i].value && addresses[i].value) {
                    activities.push({
                        name: names[i].value, 
                        address: addresses[i].value,
                        category: categories[i].value
                    });
                }
            }

            try {
                // On appelle l'API Dockerisée
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

        function displayResult(data) {
            try {
                let html = "<h2>📅 Votre itinéraire optimisé :</h2>";
                // On boucle sur chaque jour (Jour 1, Jour 2...)
                for (const [day, activities] of Object.entries(data)) {
                    html += `<div class="day-card"><strong>${day}</strong><ul>`;
                    
                    // ICI : On boucle sur la liste d'objets
                    activities.forEach(act => {
                        // act.name, act.category et act.address doivent exister
                        html += `<li><strong>${act.name}</strong> (${act.category}) - ${act.address}</li>`;
                    });
                    
                    html += `</ul></div>`;
                }
                document.getElementById('result').innerHTML = html;
            } catch (e) {
                console.error("Erreur d'affichage :", e);
                document.getElementById('result').innerHTML = "<p style='color:red;'>Erreur lors de l'affichage des données.</p>";
            }
}