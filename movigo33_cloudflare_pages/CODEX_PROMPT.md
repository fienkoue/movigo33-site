# Prompt Codex conseillé

Tu travailles sur un site statique Python/Jinja2 déployé sur Netlify.
Objectif : améliorer le SEO local de Movigo33 pour "location utilitaire Bordeaux", "location utilitaire Talence", "location utilitaire Pessac", "location utilitaire Bègles" et "location utilitaire Mérignac".

Contraintes :
- Ne casse pas la génération `python update_index.py`.
- Le dossier publié Netlify est `dist/`.
- Les données doivent rester dans `data/*.json`.
- Les templates sont dans `templates/`.
- Ajouter du contenu unique par page locale, éviter le duplicate content.
- Garder des balises title < 60 caractères si possible et meta description < 155 caractères.
- Conserver sitemap.xml, robots.txt, canonical, JSON-LD et pages 404/contact/merci.

Tâches prioritaires :
1. Enrichir `data/villes.json` avec des quartiers, cas d’usage et FAQ spécifiques par ville.
2. Adapter `templates/local.html` pour afficher ce contenu unique.
3. Ajouter 5 articles de blog longue traîne dans `data/posts.json`.
4. Vérifier que `python update_index.py` génère sans erreur.
5. Ne pas utiliser de framework lourd.
