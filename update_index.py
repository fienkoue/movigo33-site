import os
import json
import shutil
import datetime
import re
from html import escape
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
DIST_DIR = BASE_DIR / "dist"
SITE_URL = os.environ.get("SITE_URL", "https://movigo33.com").rstrip("/")
SITE_NAME = "Movigo33"
IMAGES_DIR = STATIC_DIR / "images"
VERSION_SUFFIX_RE = re.compile(r"-v\d+$")

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True, trim_blocks=True, lstrip_blocks=True)

def preferred_webp_filename(image_file):
    image_path = IMAGES_DIR / image_file
    stem = image_path.stem
    candidate_stems = [VERSION_SUFFIX_RE.sub("", stem), stem]

    for candidate_stem in dict.fromkeys(candidate_stems):
        candidate = IMAGES_DIR / f"{candidate_stem}.webp"
        if candidate.exists():
            return candidate.name
    return ""

def annotate_image_webp(item, image_key="image_file", require_exists=True):
    image_file = item.get(image_key, "")
    if not image_file:
        item["image_webp"] = ""
        return item

    if not (IMAGES_DIR / image_file).exists():
        if require_exists:
            raise FileNotFoundError(f"Image referenced by {image_key} does not exist: {image_file}")
        item["image_webp"] = ""
        return item

    item["image_webp"] = preferred_webp_filename(image_file)
    return item

def annotate_collection_images(collection, image_key="image_file", require_exists=True):
    if isinstance(collection, dict):
        for items in collection.values():
            for item in items:
                annotate_image_webp(item, image_key, require_exists)
    else:
        for item in collection:
            annotate_image_webp(item, image_key, require_exists)
    return collection

def ensure_clean_dist():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STATIC_DIR, DIST_DIR / "static")
    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")

def load_json(name):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def jsonld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

def seo_text(text, max_length=155):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= max_length:
        return text

    shortened = text[: max_length - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{shortened}…"

def image_url(item, image_key="image_file"):
    return f"{SITE_URL}/static/images/{item.get('image_webp') or item[image_key]}"

def product_schema(item, page_url, name=None, category=None, offer_url=None, item_condition="https://schema.org/NewCondition"):
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": f"{page_url}#product",
        "name": name or item["nom"],
        "description": item.get("description", ""),
        "image": image_url(item),
        "sku": item.get("id") or item.get("slug"),
        "category": category or item.get("categorie", ""),
        "brand": {"@type": "Brand", "name": SITE_NAME},
        "offers": {
            "@type": "Offer",
            "url": offer_url or page_url,
            "price": item["prix"],
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock",
            "itemCondition": item_condition,
            "seller": {"@type": "Organization", "name": SITE_NAME}
        }
    }

def render(template, output, **ctx):
    defaults = {
        "site_url": SITE_URL,
        "schema_json": "",
        "og_type": "website",
    }
    defaults.update(ctx)
    html = env.get_template(template).render(**defaults)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print("✅", output.relative_to(BASE_DIR))

def flatten(data):
    result = []
    for cat, items in data.items():
        for item in items:
            copy = dict(item)
            copy["categorie"] = cat
            result.append(copy)
    return result

def generate_sitemap(urls):
    now = datetime.date.today().isoformat()
    rows = []
    for loc, priority, changefreq in urls:
        rows.append(
            "  <url>"
            f"<loc>{escape(loc)}</loc>"
            f"<lastmod>{now}</lastmod>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority>"
            "</url>"
        )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>"
    (DIST_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")

def main():
    ensure_clean_dist()
    current_year = datetime.datetime.now().year
    vehicules = load_json("vehicules.json")
    produits = load_json("produits.json")
    villes = load_json("villes.json")
    posts = load_json("posts.json")

    annotate_collection_images(vehicules)
    annotate_collection_images(produits)
    annotate_collection_images(posts, "image")

    urls = [(SITE_URL + "/", "1.0", "weekly")]

    served_cities = [ville["nom"] for ville in villes]
    home_schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": f"{SITE_URL}/#localbusiness",
        "name": SITE_NAME,
        "url": SITE_URL + "/",
        "description": "Location d’utilitaires et sélection d’accessoires pratiques pour Bordeaux Métropole.",
        "areaServed": [
            {"@type": "City", "name": city} for city in served_cities
        ],
        "knowsAbout": [
            "location utilitaire Bordeaux",
            "déménagement Bordeaux Métropole",
            "location camion",
            "accessoires pratiques"
        ],
        "makesOffer": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Location utilitaire à Bordeaux Métropole"}},
            {"@type": "Offer", "itemOffered": {"@type": "Product", "name": "Accessoires pratiques Movigo33"}}
        ]
    }
    render("index.html", DIST_DIR / "index.html",
        meta_title="Location utilitaire Bordeaux Métropole | Movigo33",
        meta_description="Movigo33 compare utilitaires, citadines et accessoires pratiques à Bordeaux, Talence, Bègles, Pessac et Mérignac pour préparer votre trajet ou déménagement.",
        canonical_url=SITE_URL + "/", schema_json=jsonld(home_schema),
        vehicules=vehicules, produits=produits, villes=villes, posts=posts, current_year=current_year)

    render("contact.html", DIST_DIR / "contact.html",
        meta_title="Contact Movigo33 | Demande location ou boutique",
        meta_description="Une question sur un utilitaire, une citadine ou un produit pratique ? Contactez Movigo33 pour préparer votre besoin à Bordeaux Métropole.",
        canonical_url=SITE_URL + "/contact.html", current_year=current_year)
    urls.append((SITE_URL + "/contact.html", "0.5", "yearly"))

    render("merci.html", DIST_DIR / "merci.html",
        meta_title="Message bien envoyé | Movigo33",
        meta_description="Votre demande a bien été transmise à Movigo33. Nous revenons vers vous pour votre location ou votre question boutique.",
        canonical_url=SITE_URL + "/merci.html", current_year=current_year)

    render("404.html", DIST_DIR / "404.html",
        meta_title="Page introuvable | Retour Movigo33",
        meta_description="Cette page Movigo33 est introuvable. Retrouvez les véhicules, pages locales, conseils et produits pratiques depuis l’accueil.",
        canonical_url=SITE_URL + "/404.html", current_year=current_year)

    for v in flatten(vehicules):
        page_url = f"{SITE_URL}/vehicules/{v['slug']}.html"
        schema = product_schema(
            v,
            page_url,
            name=f"Location {v['nom']} à {v['ville']}",
            category="location de véhicule",
            offer_url=v.get("url") or page_url,
            item_condition="https://schema.org/UsedCondition"
        )
        render("vehicule.html", DIST_DIR / "vehicules" / f"{v['slug']}.html",
            meta_title=f"Location {v['nom']} {v['ville']} dès {v['prix']} €/jour",
            meta_description=seo_text(f"Réservez un {v['nom']} à {v['ville']} près de Bordeaux : {v['description']} Tarif indicatif dès {v['prix']} €/jour."),
            canonical_url=page_url, og_type="product",
            schema_json=jsonld(schema), vehicule=v, current_year=current_year)
        urls.append((f"{SITE_URL}/vehicules/{v['slug']}.html", "0.8", "weekly"))

    for p in flatten(produits):
        page_url = f"{SITE_URL}/boutique/{p['slug']}.html"
        schema = product_schema(
            p,
            page_url,
            category=f"boutique {p['categorie'].replace('_', ' ')}",
            offer_url=p.get("url") or page_url
        )
        render("produit.html", DIST_DIR / "boutique" / f"{p['slug']}.html",
            meta_title=f"{p['nom']} dès {p['prix']:.2f} € | Boutique Movigo33",
            meta_description=seo_text(f"Découvrez {p['nom']} dans la boutique Movigo33 : {p.get('description', '')} Prix indicatif {p['prix']:.2f} €."),
            canonical_url=page_url, og_type="product",
            schema_json=jsonld(schema), produit=p, current_year=current_year)
        urls.append((f"{SITE_URL}/boutique/{p['slug']}.html", "0.7", "monthly"))

    for ville in villes:
        faq_schema = {
            "@context":"https://schema.org",
            "@type":"FAQPage",
            "mainEntity":[
                {"@type":"Question","name":f"Quel utilitaire choisir pour un déménagement à {ville['nom']} ?","acceptedAnswer":{"@type":"Answer","text":"Pour quelques cartons ou petits meubles, un utilitaire compact peut suffire. Pour un gros volume, privilégiez un Boxer, Jumper ou équivalent."}},
                {"@type":"Question","name":"Comment réduire le coût de location ?","acceptedAnswer":{"@type":"Answer","text":"Réservez tôt, choisissez un véhicule proche de votre point de départ et estimez bien le volume pour éviter les allers-retours."}}
            ]
        }
        render("local.html", DIST_DIR / f"location-utilitaire-{ville['slug']}.html",
            meta_title=f"Location utilitaire {ville['nom']} | Véhicules près de Bordeaux",
            meta_description=seo_text(f"{ville['intro']} Comparez les véhicules proches, tarifs indicatifs et conseils Movigo33 pour louer à {ville['nom']} sans perdre de temps."),
            canonical_url=f"{SITE_URL}/location-utilitaire-{ville['slug']}.html",
            schema_json=jsonld(faq_schema), ville=ville, vehicules=vehicules, current_year=current_year)
        urls.append((f"{SITE_URL}/location-utilitaire-{ville['slug']}.html", "0.9", "weekly"))

    for post in posts:
        schema = {
            "@context":"https://schema.org",
            "@type":"Article",
            "headline":post["titre"],
            "description":post.get("excerpt",""),
            "image":f"{SITE_URL}/static/images/{post.get('image_webp') or post['image']}",
            "author":{"@type":"Organization","name":SITE_NAME},
            "publisher":{"@type":"Organization","name":SITE_NAME}
        }
        render("post.html", DIST_DIR / "blog" / f"{post['slug']}.html",
            meta_title=f"{post['titre']} | Conseils Movigo33",
            meta_description=seo_text(f"{post.get('excerpt', '')} Guide pratique Movigo33 pour mieux organiser votre location, transport ou déménagement à Bordeaux."),
            canonical_url=f"{SITE_URL}/blog/{post['slug']}.html", og_type="article",
            schema_json=jsonld(schema), post=post, current_year=current_year)
        urls.append((f"{SITE_URL}/blog/{post['slug']}.html", "0.6", "monthly"))

    (DIST_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (DIST_DIR / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN

/*.html
  Cache-Control: public, max-age=0, must-revalidate

/static/*
  Cache-Control: public, max-age=31536000, immutable

/assets/*
  Cache-Control: public, max-age=31536000, immutable
""", encoding="utf-8")
    (DIST_DIR / "_redirects").write_text("""https://www.movigo33.com/* https://movigo33.com/:splat 301!
http://movigo33.com/* https://movigo33.com/:splat 301!
http://www.movigo33.com/* https://movigo33.com/:splat 301!
""", encoding="utf-8")
    generate_sitemap(urls)
    print("\n🎉 Site SEO généré dans dist/")

if __name__ == "__main__":
    main()
