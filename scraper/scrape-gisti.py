#!/usr/bin/env python3
"""
GISTI Website Scraper v2
========================
Scrapes content from gisti.org for the redesign prototype.
Rate-limited (1 request per 2 seconds) with local cache.
Better URL targeting for the current GISTI site structure.

Usage:
    pip install -r requirements.txt
    python scrape-gisti.py

Output: JSON files in ../content/
"""

import json
import os
import time
import hashlib
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://www.gisti.org"
CACHE_DIR = Path(__file__).parent / ".cache"
OUTPUT_DIR = Path(__file__).parent.parent / "content"
RATE_LIMIT = 2  # seconds between requests
USER_AGENT = "GISTI-Redesign-Scraper/2.0 (educational prototype)"
TIMEOUT = 45

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
last_request_time = 0


def get_cache_path(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.html"


def fetch(url):
    global last_request_time
    cache_path = get_cache_path(url)
    if cache_path.exists():
        print(f"  [cache] {url}")
        return cache_path.read_text(encoding="utf-8")

    elapsed = time.time() - last_request_time
    if elapsed < RATE_LIMIT:
        time.sleep(RATE_LIMIT - elapsed)

    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        last_request_time = time.time()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(response.text, encoding="utf-8")
        print(f"  [fetch] {url}")
        return response.text
    except requests.RequestException as e:
        print(f"  [error] {url}: {e}")
        return None


def parse(html):
    return BeautifulSoup(html, "lxml")


def save_json(data, filepath):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> Saved {filepath} ({len(data)} items)")


def clean_text(text):
    """Clean scraped text: collapse whitespace, strip."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# --- Scrapers ---

def scrape_homepage():
    """Scrape the homepage for main content and navigation links."""
    print("\n[1/7] Scraping homepage...")
    html = fetch(BASE_URL)
    if not html:
        return {}

    soup = parse(html)
    data = {
        "title": "",
        "tagline": "",
        "featured_articles": [],
        "navigation_links": [],
    }

    # Get main title/tagline
    title_el = soup.select_one("h1, .site-title, #logo")
    if title_el:
        data["title"] = clean_text(title_el.get_text())

    # Get featured/latest content from homepage
    for link in soup.select("#contenu a, .une a, .articles a, main a"):
        href = link.get("href", "")
        title = clean_text(link.get_text())
        if title and len(title) > 5 and "article" in href:
            full_url = urljoin(BASE_URL, href)
            if full_url not in [a["url"] for a in data["featured_articles"]]:
                data["featured_articles"].append({
                    "url": full_url,
                    "title": title[:200],
                })

    # Get nav links
    for link in soup.select("nav a, .menu a, #nav a"):
        href = link.get("href", "")
        title = clean_text(link.get_text())
        if title and href:
            data["navigation_links"].append({
                "url": urljoin(BASE_URL, href),
                "title": title,
            })

    save_json(data, OUTPUT_DIR / "homepage.json")
    return data


def scrape_articles():
    """Scrape articles from multiple entry points."""
    print("\n[2/7] Scraping articles...")
    articles = []
    seen_urls = set()

    # Try various section URLs (GISTI SPIP structure)
    entry_pages = [
        f"{BASE_URL}/spip.php?rubrique3",    # Resources/adresses
        f"{BASE_URL}/spip.php?rubrique19",   # Publications section
        f"{BASE_URL}/spip.php?rubrique77",   # About section
        f"{BASE_URL}/",                       # Homepage
    ]

    for page_url in entry_pages:
        html = fetch(page_url)
        if not html:
            continue

        soup = parse(html)
        article_urls = []

        for link in soup.select("a[href*='article']"):
            href = link.get("href", "")
            if "article" in href and href not in seen_urls:
                full_url = urljoin(BASE_URL, href)
                if full_url not in seen_urls:
                    article_urls.append(full_url)
                    seen_urls.add(full_url)

        # Scrape up to 8 articles per section
        for url in article_urls[:8]:
            article = scrape_single_article(url)
            if article and article["title"] != "Sans titre":
                articles.append(article)

    # Deduplicate
    unique = {}
    for a in articles:
        if a["url"] not in unique:
            unique[a["url"]] = a
    articles = list(unique.values())

    save_json(articles, OUTPUT_DIR / "articles" / "all.json")
    return articles


def scrape_single_article(url):
    html = fetch(url)
    if not html:
        return None

    soup = parse(html)

    # Try multiple selectors for SPIP pages
    title = ""
    for sel in ["h1.titre", ".titre-article", "h1.entry-title", "#contenu h1", "h1"]:
        el = soup.select_one(sel)
        if el:
            title = clean_text(el.get_text())
            break

    body = ""
    body_html = ""
    for sel in [".texte", ".article-texte", ".entry-content", "#contenu .texte"]:
        el = soup.select_one(sel)
        if el:
            body_html = str(el)
            body = clean_text(el.get_text())[:1000]
            break

    date = ""
    for sel in [".date", ".date-publication", "time", ".post-date"]:
        el = soup.select_one(sel)
        if el:
            date = clean_text(el.get_text())
            break

    # Extract keywords/mots-cles
    keywords = []
    for kw in soup.select(".mots-cles a, .tags a, .mot-cle a, .groupe-mots a"):
        kw_text = clean_text(kw.get_text())
        if kw_text and kw_text not in keywords:
            keywords.append(kw_text)

    # Extract rubrique/section
    rubrique = ""
    for sel in [".rubrique a", ".fil-ariane a", "nav.breadcrumb a"]:
        el = soup.select_one(sel)
        if el:
            rubrique = clean_text(el.get_text())
            break

    if not title:
        return None

    return {
        "url": url,
        "title": title,
        "date": date,
        "rubrique": rubrique,
        "body_text": body,
        "body_html": body_html,
        "keywords": keywords,
    }


def scrape_dossiers():
    """Scrape dossier/rubrique structure."""
    print("\n[3/7] Scraping dossiers...")
    dossiers = []
    seen = set()

    # The GISTI site organizes by years under rubrique77
    # Let's also try to find thematic rubriques
    entry_urls = [
        f"{BASE_URL}/spip.php?rubrique77",
        f"{BASE_URL}/spip.php?rubrique3",
        f"{BASE_URL}/",
    ]

    for entry_url in entry_urls:
        html = fetch(entry_url)
        if not html:
            continue

        soup = parse(html)

        for link in soup.select("a[href*='rubrique']"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            if not title or len(title) < 3 or "#" in href:
                continue

            full_url = urljoin(BASE_URL, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            dossiers.append({
                "url": full_url,
                "title": title,
            })

    # Deduplicate by URL and enrich with article counts
    unique = {}
    for d in dossiers:
        if d["url"] not in unique and d["title"] not in ["", " "]:
            unique[d["url"]] = d

    enriched = []
    for url, d in list(unique.items())[:19]:
        html = fetch(url)
        article_count = 0
        description = ""
        if html:
            soup = parse(html)
            article_count = len(set(
                urljoin(BASE_URL, a.get("href", ""))
                for a in soup.select("a[href*='article']")
            ))
            # Try to get description
            desc_el = soup.select_one(".texte p, .descriptif, .description")
            if desc_el:
                description = clean_text(desc_el.get_text())[:300]

        enriched.append({
            "url": d["url"],
            "title": d["title"],
            "article_count": article_count,
            "description": description,
        })

    save_json(enriched, OUTPUT_DIR / "dossiers" / "all.json")
    return enriched


def scrape_publications():
    """Scrape the publications catalog (Plein Droit, notes, cahiers)."""
    print("\n[4/7] Scraping publications...")
    publications = []
    seen = set()

    # Plein Droit listing
    html = fetch(f"{BASE_URL}/spip.php?rubrique38")
    if html:
        soup = parse(html)
        for link in soup.select("a"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            full_url = urljoin(BASE_URL, href)

            if title and len(title) > 3 and full_url not in seen:
                pub_type = "Plein Droit" if "plein" in title.lower() or "rubrique38" in href else "Publication"
                seen.add(full_url)
                publications.append({
                    "url": full_url,
                    "title": title,
                    "type": pub_type,
                })

    # Notes pratiques
    html = fetch(f"{BASE_URL}/spip.php?rubrique47")
    if html:
        soup = parse(html)
        for link in soup.select("a[href*='article']"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            full_url = urljoin(BASE_URL, href)

            if title and len(title) > 5 and full_url not in seen:
                seen.add(full_url)
                publications.append({
                    "url": full_url,
                    "title": title,
                    "type": "Note pratique",
                })

    # Also try general publications
    html = fetch(f"{BASE_URL}/spip.php?rubrique19")
    if html:
        soup = parse(html)
        for link in soup.select("a[href*='article']"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            full_url = urljoin(BASE_URL, href)

            if title and len(title) > 5 and full_url not in seen:
                seen.add(full_url)
                publications.append({
                    "url": full_url,
                    "title": title,
                    "type": "Publication",
                })

    save_json(publications, OUTPUT_DIR / "publications" / "all.json")
    return publications


def scrape_formations():
    """Scrape the formations catalog."""
    print("\n[5/7] Scraping formations...")
    formations = []
    seen = set()

    # Try the main formations page
    for url in [f"{BASE_URL}/formations", f"{BASE_URL}/spip.php?rubrique20",
                f"{BASE_URL}/spip.php?page=formations"]:
        html = fetch(url)
        if not html:
            continue

        soup = parse(html)

        for link in soup.select("a"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            full_url = urljoin(BASE_URL, href)

            # Filter to article links with meaningful titles
            if ("article" in href and title and len(title) > 10
                    and full_url not in seen
                    and not title.startswith("20")):  # skip date-only entries
                seen.add(full_url)

                # Try to detect format
                fmt = "presentiel"
                title_lower = title.lower()
                if "webinaire" in title_lower or "distanciel" in title_lower or "en ligne" in title_lower:
                    fmt = "distanciel"

                formations.append({
                    "url": full_url,
                    "title": title,
                    "format": fmt,
                })

    # Enrich first few with detail scraping
    for i, f in enumerate(formations[:13]):
        html = fetch(f["url"])
        if html:
            soup = parse(html)
            text_el = soup.select_one(".texte, .article-texte")
            if text_el:
                text = clean_text(text_el.get_text())
                f["description"] = text[:400]

                # Try to extract dates
                date_match = re.search(r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}', text, re.IGNORECASE)
                if date_match:
                    f["date"] = date_match.group(0)

                # Try to extract price
                price_match = re.search(r'(\d+)\s*€', text)
                if price_match:
                    f["price"] = price_match.group(0)

                # Duration
                dur_match = re.search(r'(\d+)\s*jour', text, re.IGNORECASE)
                if dur_match:
                    f["duration"] = dur_match.group(0)

    save_json(formations, OUTPUT_DIR / "formations" / "all.json")
    return formations


def scrape_pratique():
    """Scrape practical resources (modeles de recours, etc.)."""
    print("\n[6/7] Scraping practical resources...")
    resources = []
    seen = set()

    # Try to find the practical resources section
    for url in [f"{BASE_URL}/spip.php?rubrique3",
                f"{BASE_URL}/spip.php?rubrique1",
                f"{BASE_URL}/spip.php?article136"]:
        html = fetch(url)
        if not html:
            continue

        soup = parse(html)

        for link in soup.select("a"):
            href = link.get("href", "")
            title = clean_text(link.get_text())
            full_url = urljoin(BASE_URL, href)

            if title and len(title) > 5 and full_url not in seen:
                seen.add(full_url)
                resources.append({
                    "url": full_url,
                    "title": title,
                })

    save_json(resources, OUTPUT_DIR / "pratique" / "all.json")
    return resources


def scrape_keywords():
    """Try to extract keywords from scraped articles."""
    print("\n[7/7] Building keywords from scraped content...")

    keywords = {}

    # Read previously scraped articles
    articles_path = OUTPUT_DIR / "articles" / "all.json"
    if articles_path.exists():
        with open(articles_path, encoding="utf-8") as f:
            articles = json.load(f)
        for article in articles:
            for kw in article.get("keywords", []):
                kw = kw.strip()
                if kw:
                    keywords[kw] = keywords.get(kw, 0) + 1

    # Also try to scrape the keywords page directly
    for url in [f"{BASE_URL}/spip.php?page=mots",
                f"{BASE_URL}/spip.php?rubrique50"]:
        html = fetch(url)
        if not html:
            continue

        soup = parse(html)
        for link in soup.select("a[href*='mot'], a[href*='keyword']"):
            word = clean_text(link.get_text())
            if word and len(word) > 1 and len(word) < 80:
                count_el = link.find_next(string=re.compile(r'\(\d+\)'))
                count = 1
                if count_el:
                    match = re.search(r'\((\d+)\)', count_el)
                    if match:
                        count = int(match.group(1))
                keywords[word] = max(keywords.get(word, 0), count)

    save_json(keywords, OUTPUT_DIR / "keywords.json")
    return keywords


# --- Main ---

def main():
    print("=" * 60)
    print("GISTI Website Scraper v2")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Cache:    {CACHE_DIR}")
    print(f"Output:   {OUTPUT_DIR}")
    print(f"Rate:     {RATE_LIMIT}s between requests")

    for subdir in ["articles", "dossiers", "publications", "formations", "pratique"]:
        (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)

    homepage = scrape_homepage()
    articles = scrape_articles()
    dossiers = scrape_dossiers()
    publications = scrape_publications()
    formations = scrape_formations()
    pratique = scrape_pratique()
    keywords = scrape_keywords()

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"  Homepage featured: {len(homepage.get('featured_articles', []))}")
    print(f"  Articles:          {len(articles)}")
    print(f"  Dossiers:          {len(dossiers)}")
    print(f"  Publications:      {len(publications)}")
    print(f"  Formations:        {len(formations)}")
    print(f"  Practical res.:    {len(pratique)}")
    print(f"  Keywords:          {len(keywords)}")
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
