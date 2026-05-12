# Movigo33 - Site PRO Cloudflare Pages

## Contenu
- Homepage SEO
- Pages véhicules SEO
- Pages boutique
- Pages locales automatiques (Bordeaux, Talence, Pessac, Mérignac, Bègles)
- Blog
- Sitemap XML
- Robots.txt
- Headers Cloudflare Pages
- Redirects www/http vers https://movigo33.com

## Installation
```bash
py -m pip install -r requirements.txt
py update_index.py
```

Déploie ensuite le contenu du dossier `dist/` sur Cloudflare Pages.

## Domaine
Dans Cloudflare Pages, ajoute `movigo33.com` comme domaine principal.
Utilise la configuration indiquée dans `cloudflare.toml` : commande de build `python -m pip install -r requirements.txt && python update_index.py`, dossier de sortie `dist` et variable `SITE_URL=https://movigo33.com`.

## Important
Les images fournies sont des placeholders. Remplace-les dans `static/images/` par tes vraies photos.
