#!/usr/bin/env python3
"""
Content Injector — GISTI Redesign
=================================
Reads scraped JSON content and injects it into HTML pages.

Usage:
    python inject-content.py
"""

import json
import re
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def clean(text):
    """Clean text for HTML insertion."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def make_card_html(article, index=0):
    """Generate a card HTML block from article data."""
    title = escape(clean(article.get("title", "Sans titre")))
    date = escape(clean(article.get("date", "")))
    body = escape(clean(article.get("body_text", ""))[:180])
    rubrique = escape(clean(article.get("rubrique", "")))
    url = escape(article.get("url", "article.html"))

    date_html = f'<time>{date}</time>' if date else ""
    rubrique_html = f'<span>&middot;</span><span>{rubrique}</span>' if rubrique else ""

    return f'''          <article class="card">
            <div class="card__body">
              <span class="card__overline">Article</span>
              <h3 class="card__title">
                <a href="article.html">{title}</a>
              </h3>
              <p class="card__text">{body}</p>
              <div class="card__meta">
                {date_html}
                {rubrique_html}
              </div>
            </div>
          </article>'''


def make_formation_mini_html(formation):
    """Generate a formation mini card."""
    title = escape(clean(formation.get("title", "")))
    date = clean(formation.get("date", ""))
    price = escape(clean(formation.get("price", "")))
    duration = escape(clean(formation.get("duration", "")))

    # Parse date for display
    day = ""
    month = ""
    if date:
        parts = date.split()
        if len(parts) >= 2:
            day = parts[0]
            month = parts[1][:4] + "."

    meta_parts = []
    if duration:
        meta_parts.append(duration)
    meta_parts.append("Paris")
    if price:
        meta_parts.append(price)
    meta_str = " &middot; ".join(meta_parts)

    return f'''              <div class="formation-mini">
                <div class="formation-mini__date">
                  <span class="formation-mini__date-day">{escape(day) if day else "?"}</span>
                  <span class="formation-mini__date-month">{escape(month) if month else ""}</span>
                </div>
                <div>
                  <p class="formation-mini__title">{title}</p>
                  <p class="formation-mini__meta">{meta_str}</p>
                </div>
              </div>'''


def make_pub_card_html(pub):
    """Generate a publication card."""
    title = escape(clean(pub.get("title", "")))
    pub_type = escape(clean(pub.get("type", "Publication")))

    return f'''          <a href="publication-detail.html" class="pub-card" data-filter-item data-type="{pub_type.lower().replace(' ', '-')}">
            <div class="pub-card__cover-placeholder">{title[:30]}</div>
            <div class="pub-card__body">
              <span class="pub-card__type">{pub_type}</span>
              <h3 class="pub-card__title">{title}</h3>
            </div>
          </a>'''


def make_formation_card_html(formation):
    """Generate a full formation card."""
    title = escape(clean(formation.get("title", "")))
    desc = escape(clean(formation.get("description", ""))[:200])
    fmt = formation.get("format", "presentiel")
    price = escape(clean(formation.get("price", "")))
    duration = escape(clean(formation.get("duration", "")))
    date = escape(clean(formation.get("date", "")))

    fmt_label = {"presentiel": "Présentiel", "distanciel": "Distanciel", "webinaire": "Webinaire"}.get(fmt, "Présentiel")
    fmt_class = f"formation-card__format--{fmt}"

    details = []
    if duration:
        details.append(f'<span class="formation-card__detail">{duration}</span>')
    if date:
        details.append(f'<span class="formation-card__detail">{date}</span>')
    if price:
        details.append(f'<span class="formation-card__detail formation-card__price">{price}</span>')

    return f'''          <div class="formation-card" data-filter-item>
            <div class="formation-card__header">
              <h3 class="formation-card__title">{title}</h3>
              <span class="formation-card__format {fmt_class}">{fmt_label}</span>
            </div>
            <p class="formation-card__desc">{desc}</p>
            <div class="formation-card__details">
              {chr(10).join(details)}
              <span class="formation-card__places">Places disponibles</span>
            </div>
          </div>'''


def inject_homepage():
    """Inject real content into index.html."""
    print("Injecting into index.html...")

    html_path = BASE_DIR / "index.html"
    html = html_path.read_text(encoding="utf-8")

    # Load data
    articles = load_json(CONTENT_DIR / "articles" / "all.json")
    formations = load_json(CONTENT_DIR / "formations" / "all.json")
    homepage = load_json(CONTENT_DIR / "homepage.json")

    # --- Inject "À la une" cards ---
    # Find the featured articles grid and replace with real content
    featured = [a for a in articles if a.get("title") and len(a["title"]) > 10][:3]
    if not featured and homepage and isinstance(homepage, dict):
        # Use homepage featured articles
        for fa in homepage.get("featured_articles", [])[:3]:
            featured.append({"title": fa["title"], "url": fa["url"], "body_text": "", "date": ""})

    if featured:
        cards_html = "\n\n".join(make_card_html(a, i) for i, a in enumerate(featured))
        # Replace the 3 existing À la une cards
        pattern = r'(class="grid grid-3 reveal">\s*\n)(.*?)(</div>\s*</div>\s*</section>\s*\n\s*<!-- Dossiers actifs)'
        replacement = rf'\g<1>{cards_html}\n\g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    # --- Inject formations ---
    real_formations = [f for f in formations if f.get("title") and len(f["title"]) > 10 and not f["title"].startswith("20")][:4]
    if real_formations:
        formations_html = "\n\n".join(make_formation_mini_html(f) for f in real_formations)
        pattern = r'(class="flex flex-col gap-sm">\s*\n)(.*?)(</div>\s*</div>\s*</div>\s*</div>\s*</section>\s*\n\s*<!-- CTA Soutenir)'
        replacement = rf'\g<1>{formations_html}\n\g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    html_path.write_text(html, encoding="utf-8")
    print(f"  -> Updated with {len(featured)} articles, {len(real_formations)} formations")


def inject_formations():
    """Inject real formations into formations.html."""
    print("Injecting into formations.html...")

    html_path = BASE_DIR / "formations.html"
    if not html_path.exists():
        print("  -> formations.html not found, skipping")
        return

    html = html_path.read_text(encoding="utf-8")
    formations = load_json(CONTENT_DIR / "formations" / "all.json")

    real = [f for f in formations if f.get("title") and len(f["title"]) > 10 and not f["title"].startswith("20")][:6]
    if real:
        cards_html = "\n\n".join(make_formation_card_html(f) for f in real)
        pattern = r'(data-filter-container[^>]*>\s*\n)(.*?)(</div>\s*</section>\s*\n\s*<!-- Nos formats|</div>\s*\n\s*</div>\s*\n\s*</section>\s*\n\s*<!-- Nos formats)'
        new_html = re.sub(pattern, rf'\g<1>{cards_html}\n\g<3>', html, flags=re.DOTALL)
        if new_html != html:
            html_path.write_text(new_html, encoding="utf-8")
            print(f"  -> Updated with {len(real)} formations")
        else:
            print("  -> Pattern not matched, no changes")
    else:
        print("  -> No formations data to inject")


def inject_publications():
    """Inject real publications into publications.html."""
    print("Injecting into publications.html...")

    html_path = BASE_DIR / "publications.html"
    if not html_path.exists():
        print("  -> publications.html not found, skipping")
        return

    html = html_path.read_text(encoding="utf-8")
    publications = load_json(CONTENT_DIR / "publications" / "all.json")

    # Filter for meaningful publications
    real = [p for p in publications
            if p.get("title")
            and len(p["title"]) > 5
            and p["title"].lower() not in ["plein droit", "abonnez-vous", "faire un don",
                                            "nous contacter", "mentions légales"]][:12]

    if real:
        cards_html = "\n\n".join(make_pub_card_html(p) for p in real)
        pattern = r'(data-filter-container[^>]*>\s*\n)(.*?)(</div>\s*\n\s*<!-- Pagination)'
        new_html = re.sub(pattern, rf'\g<1>{cards_html}\n\g<3>', html, flags=re.DOTALL)
        if new_html != html:
            html_path.write_text(new_html, encoding="utf-8")
            print(f"  -> Updated with {len(real)} publications")
        else:
            print("  -> Pattern not matched, no changes")
    else:
        print("  -> No publications data to inject")


def inject_article():
    """Inject a real article into article.html."""
    print("Injecting into article.html...")

    html_path = BASE_DIR / "article.html"
    html = html_path.read_text(encoding="utf-8")
    articles = load_json(CONTENT_DIR / "articles" / "all.json")

    # Find the richest article (most body text)
    best = None
    for a in articles:
        body = a.get("body_text", "")
        if body and len(body) > 200:
            if not best or len(body) > len(best.get("body_text", "")):
                best = a

    if best:
        title = escape(clean(best.get("title", "")))
        date = escape(clean(best.get("date", "")))

        # Inject title
        if title:
            html = re.sub(
                r'(<h1 class="article-header__title">)(.*?)(</h1>)',
                rf'\1{title}\3',
                html
            )

        # Inject keywords
        keywords = best.get("keywords", [])
        if keywords:
            tags_html = "\n".join(
                f'              <a href="recherche.html?tag={escape(kw.lower().replace(" ", "-"))}" class="tag">{escape(kw)}</a>'
                for kw in keywords[:10]
            )
            html = re.sub(
                r'(class="tag-list">\s*\n)(.*?)(</div>\s*\n\s*</div>\s*\n\s*<!-- Related)',
                rf'\1{tags_html}\n\g<3>',
                html,
                flags=re.DOTALL
            )

        html_path.write_text(html, encoding="utf-8")
        print(f"  -> Updated with article: {title[:60]}")
    else:
        print("  -> No suitable article found")


def inject_dossiers():
    """Inject real dossier data into dossiers.html."""
    print("Injecting into dossiers.html...")

    html_path = BASE_DIR / "dossiers.html"
    if not html_path.exists():
        print("  -> dossiers.html not found, skipping")
        return

    html = html_path.read_text(encoding="utf-8")
    dossiers = load_json(CONTENT_DIR / "dossiers" / "all.json")

    # Filter meaningful dossiers
    real = [d for d in dossiers
            if d.get("title")
            and len(d["title"]) > 3
            and d["title"] not in ["Aider le Gisti"]]

    if not real:
        print("  -> No dossier data to inject")
        return

    # Update the page title count
    count = len(real)
    html = re.sub(
        r'(\d+) dossiers thématiques',
        f'{count} dossiers thématiques',
        html
    )

    html_path.write_text(html, encoding="utf-8")
    print(f"  -> Updated with {count} dossiers metadata")


def main():
    print("=" * 60)
    print("Content Injection")
    print("=" * 60)

    inject_homepage()
    inject_article()
    inject_formations()
    inject_publications()
    inject_dossiers()

    print("\n" + "=" * 60)
    print("INJECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
