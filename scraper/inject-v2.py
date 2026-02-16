#!/usr/bin/env python3
"""
Content Injector v2 — GISTI Redesign
=====================================
Targeted injection of real Plein Droit titles, formations, and homepage content.
"""

import json
import re
import hashlib
from pathlib import Path
from html import escape
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content"
CACHE_DIR = Path(__file__).parent / ".cache"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_cached(url):
    h = hashlib.md5(url.encode()).hexdigest()
    f = CACHE_DIR / f"{h}.html"
    if f.exists():
        return BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
    return None


def clean(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def get_plein_droit_issues():
    """Extract all Plein Droit issues from rubrique38."""
    soup = load_cached("https://www.gisti.org/spip.php?rubrique38")
    if not soup:
        return []

    issues = []
    for h2 in soup.select("h2"):
        title = clean(h2.get_text())
        if title and len(title) > 3:
            link = h2.find("a")
            href = link.get("href", "") if link else ""
            issues.append({
                "title": title,
                "url": f"https://www.gisti.org/{href}" if href else "",
            })
    return issues


def get_homepage_articles():
    """Extract featured articles from the homepage."""
    soup = load_cached("https://www.gisti.org")
    if not soup:
        return []

    articles = []
    seen = set()

    # Look for article links in the main content area
    for link in soup.select("a[href*='article']"):
        title = clean(link.get_text())
        href = link.get("href", "")

        if (title and len(title) > 15 and title not in seen
                and "article" in href
                and title.lower() not in ["faire un don", "abonnez-vous", "nous contacter"]):
            seen.add(title)
            articles.append({"title": title, "url": href})

    return articles


def get_formations():
    """Extract formations with details."""
    formations_json = load_json(CONTENT_DIR / "formations" / "all.json")
    # Filter meaningful ones
    return [f for f in formations_json
            if f.get("title")
            and len(f["title"]) > 10
            and f["title"].lower() not in ["inscription individuelle", "formations intra-structures",
                                            "catalogue des formations du gisti"]
            and not f["title"].startswith("20")]


# --- Injection functions ---

def inject_index():
    """Inject real content into index.html."""
    print("\n[1] index.html")
    path = BASE_DIR / "index.html"
    html = path.read_text(encoding="utf-8")

    # Get data
    homepage_articles = get_homepage_articles()
    formations = get_formations()
    plein_droit = get_plein_droit_issues()

    # --- Featured articles ---
    if homepage_articles:
        featured = homepage_articles[:3]
        cards = []
        types = ["Analyse", "Communiqué", "Action"]
        for i, a in enumerate(featured):
            title = escape(a["title"])
            overline = types[i % 3]
            cards.append(f'''          <article class="card">
            <div class="card__body">
              <span class="card__overline">{overline}</span>
              <h3 class="card__title">
                <a href="article.html">{title}</a>
              </h3>
              <div class="card__meta">
                <span>gisti.org</span>
              </div>
            </div>
          </article>''')

        cards_html = "\n\n".join(cards)
        pattern = r'(class="grid grid-3 reveal">\s*\n)(.*?)(</div>\s*</div>\s*</section>\s*\n\s*<!-- Dossiers actifs)'
        html = re.sub(pattern, rf'\1{cards_html}\n\3', html, flags=re.DOTALL)
        print(f"  Articles: injected {len(featured)} featured articles")

    # --- Plein Droit latest ---
    if plein_droit:
        latest = plein_droit[0]
        title = escape(latest["title"])
        # Numbering: 138 issues, latest = 140 (approx)
        num = 140
        html = re.sub(
            r'Plein Droit<br>n°\d+',
            f'Plein Droit<br>n&deg;{num}',
            html
        )
        html = re.sub(
            r'(Dernier numéro — )[^<]+',
            r'\g<1>2025',
            html
        )
        html = re.sub(
            r'(<h3 class="h4 mt-sm" style="color:var\(--color-primary-dark\)">)[^<]+(</h3>)',
            rf'\1{title}\2',
            html
        )
        print(f"  Plein Droit: {title}")

    # --- Formations ---
    if formations:
        real_f = formations[:4]
        f_cards = []
        for f in real_f:
            title = escape(clean(f.get("title", "")))
            date = clean(f.get("date", ""))
            price = escape(clean(f.get("price", "")))
            duration = escape(clean(f.get("duration", "")))

            day, month = "?", ""
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

            f_cards.append(f'''              <div class="formation-mini">
                <div class="formation-mini__date">
                  <span class="formation-mini__date-day">{escape(day)}</span>
                  <span class="formation-mini__date-month">{escape(month)}</span>
                </div>
                <div>
                  <p class="formation-mini__title">{title}</p>
                  <p class="formation-mini__meta">{" &middot; ".join(meta_parts)}</p>
                </div>
              </div>''')

        f_html = "\n\n".join(f_cards)
        pattern = r'(class="flex flex-col gap-sm">\s*\n)(.*?)(</div>\s*</div>\s*</div>\s*</div>\s*</section>\s*\n\s*<!-- CTA Soutenir)'
        html = re.sub(pattern, rf'\1{f_html}\n\3', html, flags=re.DOTALL)
        print(f"  Formations: injected {len(real_f)}")

    path.write_text(html, encoding="utf-8")


def inject_publications():
    """Inject Plein Droit issues into publications.html."""
    print("\n[2] publications.html")
    path = BASE_DIR / "publications.html"
    if not path.exists():
        print("  -> not found")
        return

    html = path.read_text(encoding="utf-8")
    issues = get_plein_droit_issues()

    if not issues:
        print("  -> no Plein Droit data")
        return

    # Generate publication cards
    cards = []
    for i, issue in enumerate(issues[:12]):
        title = escape(issue["title"])
        num = 140 - i
        cards.append(f'''          <a href="publication-detail.html" class="pub-card" data-filter-item data-type="plein-droit" data-year="2025">
            <div class="pub-card__cover-placeholder">Plein Droit<br>n&deg;{num}</div>
            <div class="pub-card__body">
              <span class="pub-card__type">Plein Droit</span>
              <h3 class="pub-card__title">{title}</h3>
              <span class="pub-card__meta">n&deg;{num}</span>
              <span class="pub-card__price">6 &euro;</span>
            </div>
          </a>''')

    cards_html = "\n\n".join(cards)
    pattern = r'(data-filter-container[^>]*>\s*\n)(.*?)(</div>\s*\n\s*<!-- Pagination)'
    new_html = re.sub(pattern, rf'\1{cards_html}\n\3', html, flags=re.DOTALL)

    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        print(f"  -> Injected {len(cards)} Plein Droit issues")
    else:
        print("  -> Pattern not matched")


def inject_publication_detail():
    """Inject latest Plein Droit into publication-detail.html."""
    print("\n[3] publication-detail.html")
    path = BASE_DIR / "publication-detail.html"
    if not path.exists():
        print("  -> not found")
        return

    html = path.read_text(encoding="utf-8")
    issues = get_plein_droit_issues()

    if issues:
        title = escape(issues[0]["title"])
        html = re.sub(
            r'(<h1[^>]*class="pub-detail__title"[^>]*>)[^<]+(</h1>)',
            rf'\g<1>{title}\2',
            html
        )
        html = re.sub(
            r'(Plein Droit n°)\d+',
            r'\g<1>140',
            html
        )
        path.write_text(html, encoding="utf-8")
        print(f"  -> Updated with: {title}")


def inject_formations():
    """Inject real formations into formations.html."""
    print("\n[4] formations.html")
    path = BASE_DIR / "formations.html"
    if not path.exists():
        print("  -> not found")
        return

    html = path.read_text(encoding="utf-8")
    formations = get_formations()

    if not formations:
        print("  -> no formations data")
        return

    # Generate formation cards
    cards = []
    for f in formations[:6]:
        title = escape(clean(f.get("title", "")))
        desc = escape(clean(f.get("description", "Formation professionnelle continue par le GISTI."))[:200])
        fmt = f.get("format", "presentiel")
        price = escape(clean(f.get("price", "")))
        duration = escape(clean(f.get("duration", "")))
        date = escape(clean(f.get("date", "")))

        fmt_label = {"presentiel": "Présentiel", "distanciel": "Distanciel"}.get(fmt, "Présentiel")
        fmt_class = f"formation-card__format--{fmt}"

        details = []
        if duration:
            details.append(f'<span class="formation-card__detail">{duration}</span>')
        if date:
            details.append(f'<span class="formation-card__detail">{date}</span>')
        else:
            details.append('<span class="formation-card__detail">2026</span>')
        details.append('<span class="formation-card__detail">Paris 11e</span>')
        if price:
            details.append(f'<span class="formation-card__detail formation-card__price">{price}</span>')

        cards.append(f'''          <div class="formation-card" data-filter-item>
            <div class="formation-card__header">
              <h3 class="formation-card__title">{title}</h3>
              <span class="formation-card__format {fmt_class}">{fmt_label}</span>
            </div>
            <p class="formation-card__desc">{desc}</p>
            <div class="formation-card__details">
              {chr(10).join("              " + d for d in details)}
              <span class="formation-card__places">Places disponibles</span>
            </div>
          </div>''')

    cards_html = "\n\n".join(cards)

    # Try to find the grid container for formation cards
    # Look for the section after the filter bar
    pattern = r'(class="grid-auto"[^>]*data-filter-container[^>]*>\s*\n)(.*?)(</div>\s*\n\s*</div>\s*\n\s*</section>)'
    new_html = re.sub(pattern, rf'\1{cards_html}\n\3', html, flags=re.DOTALL, count=1)

    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        print(f"  -> Injected {len(cards)} formations")
    else:
        # Try alternate pattern
        pattern2 = r'(data-filter-container[^>]*>\s*\n)(.*?)(</div>\s*\n\s*</section>)'
        new_html = re.sub(pattern2, rf'\1{cards_html}\n\3', html, flags=re.DOTALL, count=1)
        if new_html != html:
            path.write_text(new_html, encoding="utf-8")
            print(f"  -> Injected {len(cards)} formations (alt pattern)")
        else:
            print("  -> Pattern not matched, writing card titles for reference:")
            for f in formations[:6]:
                print(f"     - {f['title']}")


def main():
    print("=" * 60)
    print("Content Injection v2")
    print("=" * 60)

    inject_index()
    inject_publications()
    inject_publication_detail()
    inject_formations()

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
