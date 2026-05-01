import os
import json
import shutil
import datetime
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

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

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
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{now}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>"
    (DIST_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")

def main():
    ensure_clean_dist()
    current_year = datetime.datetime.now().year
    vehicules = load_json("vehicules.json")
    produits = load_json("produits.json")
    villes = load_json("villes.json")
    posts = load_json("posts.json")

    urls = [(SITE_URL + "/", "1.0", "weekly")]

    home_schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": SITE_NAME,
        "url": SITE_URL + "/",
        "areaServed": ["Bordeaux", "Talence", "Bègles", "Pessac", "Mérignac"],
        "description": "Location utilitaire à Bordeaux Métropole et sélection de produits utiles."
    }
    render("index.html", DIST_DIR / "index.html",
        meta_title="Location utilitaire Bordeaux, Talence, Bègles | Movigo33",
        meta_description="Location utilitaire à Bordeaux Métropole : Boxer, Jumper, Kangoo et véhicules pratiques à Talence, Bègles, Pessac et Mérignac.",
        canonical_url=SITE_URL + "/", schema_json=jsonld(home_schema),
        vehicules=vehicules, produits=produits, villes=villes, posts=posts, current_year=current_year)

    render("contact.html", DIST_DIR / "contact.html",
        meta_title="Contact Movigo33 - Location utilitaire Bordeaux",
        meta_description="Contactez Movigo33 pour une location utilitaire à Bordeaux Métropole ou une question boutique.",
        canonical_url=SITE_URL + "/contact.html", current_year=current_year)
    urls.append((SITE_URL + "/contact.html", "0.5", "yearly"))

    render("merci.html", DIST_DIR / "merci.html",
        meta_title="Message envoyé - Movigo33",
        meta_description="Confirmation d’envoi de message à Movigo33.",
        canonical_url=SITE_URL + "/merci.html", current_year=current_year)

    render("404.html", DIST_DIR / "404.html",
        meta_title="Page introuvable - Movigo33",
        meta_description="Page introuvable sur le site Movigo33.",
        canonical_url=SITE_URL + "/404.html", current_year=current_year)

    for v in flatten(vehicules):
        schema = {
            "@context":"https://schema.org",
            "@type":"Product",
            "name":f"Location {v['nom']} à {v['ville']}",
            "description":v.get("description",""),
            "image":f"{SITE_URL}/static/images/{v['image_file']}",
            "offers":{"@type":"Offer","price":v["prix"],"priceCurrency":"EUR","availability":"https://schema.org/InStock","url":f"{SITE_URL}/vehicules/{v['slug']}.html"}
        }
        render("vehicule.html", DIST_DIR / "vehicules" / f"{v['slug']}.html",
            meta_title=f"Location {v['nom']} à {v['ville']} | Movigo33",
            meta_description=f"Louez un {v['nom']} à {v['ville']} près de Bordeaux. Tarif indicatif dès {v['prix']} €/jour pour déménagement ou transport.",
            canonical_url=f"{SITE_URL}/vehicules/{v['slug']}.html", og_type="product",
            schema_json=jsonld(schema), vehicule=v, current_year=current_year)
        urls.append((f"{SITE_URL}/vehicules/{v['slug']}.html", "0.8", "weekly"))

    for p in flatten(produits):
        schema = {
            "@context":"https://schema.org",
            "@type":"Product",
            "name":p["nom"],
            "description":p.get("description",""),
            "image":f"{SITE_URL}/static/images/{p['image_file']}",
            "offers":{"@type":"Offer","price":p["prix"],"priceCurrency":"EUR","availability":"https://schema.org/InStock","url":f"{SITE_URL}/boutique/{p['slug']}.html"}
        }
        render("produit.html", DIST_DIR / "boutique" / f"{p['slug']}.html",
            meta_title=f"{p['nom']} | Boutique Movigo33",
            meta_description=p.get("description", "")[:155],
            canonical_url=f"{SITE_URL}/boutique/{p['slug']}.html", og_type="product",
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
            meta_title=f"Location utilitaire {ville['nom']} | Camion & déménagement",
            meta_description=f"{ville['intro']} Comparez les véhicules proches, prix indicatifs et conseils pour louer à {ville['nom']}.",
            canonical_url=f"{SITE_URL}/location-utilitaire-{ville['slug']}.html",
            schema_json=jsonld(faq_schema), ville=ville, vehicules=vehicules, current_year=current_year)
        urls.append((f"{SITE_URL}/location-utilitaire-{ville['slug']}.html", "0.9", "weekly"))

    for post in posts:
        schema = {
            "@context":"https://schema.org",
            "@type":"Article",
            "headline":post["titre"],
            "description":post.get("excerpt",""),
            "image":f"{SITE_URL}/static/images/{post['image']}",
            "author":{"@type":"Organization","name":SITE_NAME},
            "publisher":{"@type":"Organization","name":SITE_NAME}
        }
        render("post.html", DIST_DIR / "blog" / f"{post['slug']}.html",
            meta_title=f"{post['titre']} | Blog Movigo33",
            meta_description=post.get("excerpt", "")[:155],
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
