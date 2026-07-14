# -*- coding: utf-8 -*-
"""
Collecteur pour la carte des articles abonnés de Libération en France.

Pipeline, pour chaque article trouvé dans les flux RSS :
  1. Date de publication dans la fenêtre glissante (62 jours) ;
  2. Un lieu français (gazetteer.py) présent dans les TAGS, le TITRE
     ou le CHAPÔ (description RSS) — les noms ambigus (RISKY_IN_TEXT)
     ne sont acceptés que via les tags ;
  3. Article réservé aux abonnés (détection sur la page de l'article) ;
  4. Géocodage du lieu via Nominatim (cache local, 1 req/s max) ;
  5. Écriture dans data/articles.json (dédoublonné par URL, purgé).

Usage :
  python collect.py            # collecte normale
  python collect.py --dry-run  # tout sauf l'écriture finale
  python collect.py --no-paywall-filter   # garde aussi les gratuits
  python collect.py --self-test           # test hors-ligne (fixtures)

Seules la stdlib + requests sont nécessaires.
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

from gazetteer import GAZETTEER

# ---------------------------------------------------------------- config

BASE = "https://www.liberation.fr/arc/outboundfeeds/rss"

# Flux de rubriques (larges) + flux de tags géographiques (précis).
# Les slugs inexistants renvoient un 404 : ignoré silencieusement.
CATEGORY_FEEDS = [
    "",  # flux principal "derniers articles"
    "category/politique/",
    "category/societe/",
    "category/environnement/",
    "category/economie/",
]
TAG_FEEDS = [
    # régions / territoires
    "bretagne", "corse", "occitanie", "normandie", "hauts-de-france",
    "ile-de-france", "nouvelle-aquitaine", "auvergne-rhone-alpes",
    "provence-alpes-cote-d-azur", "pays-de-la-loire", "grand-est",
    "guadeloupe", "martinique", "guyane", "la-reunion", "mayotte",
    "nouvelle-caledonie", "polynesie-francaise",
    # grandes villes
    "paris", "marseille", "lyon", "toulouse", "bordeaux", "lille",
    "nantes", "rennes", "strasbourg", "montpellier", "nice", "grenoble",
]

WINDOW_DAYS = 62          # fenêtre glissante ≈ 2 mois
REQUEST_TIMEOUT = 20
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                 "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
NOMINATIM = "https://nominatim.openstreetmap.org/search"
# fr couvre métropole + DROM ; les COM du Pacifique ont leurs codes ISO
COUNTRY_CODES = "fr,re,gp,mq,gf,yt,pm,nc,pf,wf,bl,mf"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ARTICLES_PATH = os.path.join(DATA_DIR, "articles.json")
GEOCACHE_PATH = os.path.join(DATA_DIR, "geocache.json")
PAYCACHE_PATH = os.path.join(DATA_DIR, "paywall_cache.json")

# Marqueurs "article réservé aux abonnés" cherchés dans le HTML.
# Le plus fiable est le JSON-LD isAccessibleForFree (standard Google
# pour les paywalls). Les autres sont des filets de sécurité.
PREMIUM_PATTERNS = [
    re.compile(r'"isAccessibleForFree"\s*:\s*(?:"?false"?|"False")', re.I),
    re.compile(r'"is_premium"\s*:\s*true', re.I),
    re.compile(r'"premium"\s*:\s*true', re.I),
    re.compile(r'"contentTier"\s*:\s*"(?:premium|locked|metered)"', re.I),
    re.compile(r'article[-_]?premium', re.I),
    re.compile(r'paywall', re.I),
]

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT

# ---------------------------------------------------------------- helpers


def log(msg):
    print(msg, flush=True)


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def normalize(s):
    """minuscules, sans accents, tirets/apostrophes -> espaces."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[-'’_]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


# Frontière de mot compatible accents/tirets français
_LETTER = "A-Za-zÀ-ÖØ-öø-ÿ"


def word_pattern(name):
    return re.compile(
        rf"(?<![{_LETTER}])" + re.escape(name) + rf"(?![{_LETTER}])"
    )


# Pré-compilation des regex du gazetteer (une fois)
for _e in GAZETTEER:
    _e["rx"] = word_pattern(_e["name"])
    _e["norm"] = normalize(_e["name"])

# ---------------------------------------------------------------- RSS


def fetch_feed(url):
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content
    except requests.RequestException as exc:
        log(f"  ! flux inaccessible ({exc.__class__.__name__}) : {url}")
        return None


def parse_feed(xml_bytes):
    """Extrait (titre, lien, date, description, tags) de chaque item RSS."""
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return html.unescape(el.text.strip()) if el is not None and el.text else ""

        title = text("title")
        link = text("link")
        raw_desc = text("description")
        # le chapô RSS peut contenir du HTML : on le retire
        desc = re.sub(r"<[^>]+>", " ", raw_desc)
        desc = re.sub(r"\s+", " ", desc).strip()

        tags = []
        for cat in item.findall("category"):
            if cat.text:
                tags.append(html.unescape(cat.text.strip()))
        # certains flux Arc utilisent dc:subject
        for subj in item.findall("{http://purl.org/dc/elements/1.1/}subject"):
            if subj.text:
                tags.append(html.unescape(subj.text.strip()))

        pub = None
        raw_date = text("pubDate") or text(
            "{http://purl.org/dc/elements/1.1/}date")
        if raw_date:
            try:
                pub = parsedate_to_datetime(raw_date)
            except (TypeError, ValueError):
                try:
                    pub = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except ValueError:
                    pub = None
        if pub and pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)

        if title and link:
            items.append({
                "title": title, "link": link.split("?")[0],
                "date": pub, "desc": desc, "tags": tags,
            })
    return items

# ---------------------------------------------------------------- filtres


def match_place(article):
    """Retourne (entrée_gazetteer, 'tags'|'titre'|'chapô') ou (None, None)."""
    norm_tags = {normalize(t) for t in article["tags"]}
    for e in GAZETTEER:
        if e["norm"] in norm_tags:
            return e, "tags"
    for field, label in ((article["title"], "titre"), (article["desc"], "chapô")):
        if not field:
            continue
        for e in GAZETTEER:
            if e["risky"]:
                continue
            if e["rx"].search(field):
                return e, label
    return None, None


def is_premium(url, cache, debug=False):
    """Va chercher la page de l'article et cherche un marqueur paywall."""
    if url in cache:
        return cache[url]
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        page = r.text
    except requests.RequestException as exc:
        log(f"  ! page inaccessible ({exc.__class__.__name__}), article ignoré : {url}")
        cache[url] = None   # inconnu : on ne retentera pas ce run-ci
        return None
    hit = None
    for pat in PREMIUM_PATTERNS:
        m = pat.search(page)
        if m:
            hit = pat.pattern
            break
    result = hit is not None
    if debug:
        log(f"    paywall={result} (marqueur: {hit}) {url}")
    cache[url] = result
    time.sleep(0.7)  # politesse envers liberation.fr
    return result

# ---------------------------------------------------------------- géocodage


def geocode(entry, cache):
    key = entry["query"]
    if key in cache:
        return cache[key]
    params = {
        "q": key, "format": "jsonv2", "limit": 1,
        "countrycodes": COUNTRY_CODES, "accept-language": "fr",
    }
    try:
        r = session.get(NOMINATIM, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as exc:
        log(f"  ! géocodage en échec ({exc.__class__.__name__}) : {key}")
        return None
    time.sleep(1.1)  # politique d'usage Nominatim : 1 req/s max
    if not data:
        cache[key] = None
        return None
    coords = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    cache[key] = coords
    return coords

# ---------------------------------------------------------------- main


def collect(args):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)

    articles = {a["url"]: a for a in load_json(ARTICLES_PATH, [])}
    geocache = load_json(GEOCACHE_PATH, {})
    paycache = load_json(PAYCACHE_PATH, {})

    feed_urls = [f"{BASE}/{c}?outputType=xml" for c in CATEGORY_FEEDS]
    feed_urls += [f"{BASE}/tags_slug/{t}/?outputType=xml" for t in TAG_FEEDS]

    seen, kept = 0, 0
    for url in feed_urls:
        raw = fetch_feed(url)
        if raw is None:
            continue
        items = parse_feed(raw)
        log(f"flux ok ({len(items):>3} items) {url}")
        for it in items:
            seen += 1
            if it["link"] in articles:
                continue
            if it["date"] is None or it["date"] < cutoff:
                continue
            entry, where = match_place(it)
            if entry is None:
                continue
            premium = is_premium(it["link"], paycache, debug=args.debug)
            if args.paywall_filter and premium is not True:
                continue
            coords = geocode(entry, geocache)
            if coords is None:
                continue
            articles[it["link"]] = {
                "url": it["link"],
                "id": hashlib.sha1(it["link"].encode()).hexdigest()[:12],
                "title": it["title"],
                "subtitle": it["desc"][:280],
                "date": it["date"].isoformat(),
                "place": entry["name"],
                "place_cat": entry["cat"],
                "matched_in": where,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "premium": bool(premium),
            }
            kept += 1
            log(f"  + [{entry['name']} / {where}] {it['title'][:70]}")

    # purge fenêtre glissante
    before = len(articles)
    articles = {
        u: a for u, a in articles.items()
        if datetime.fromisoformat(a["date"]) >= cutoff
    }
    purged = before - len(articles)

    out = sorted(articles.values(), key=lambda a: a["date"], reverse=True)
    log(f"\n{seen} items vus, {kept} nouveaux gardés, {purged} purgés "
        f"(> {WINDOW_DAYS} j), total carte : {len(out)}")

    if args.dry_run:
        log("--dry-run : rien n'est écrit.")
        return

    save_json(ARTICLES_PATH, out)
    save_json(GEOCACHE_PATH, geocache)
    # on ne persiste pas les statuts inconnus (None) pour retenter plus tard
    save_json(PAYCACHE_PATH, {k: v for k, v in paycache.items() if v is not None})
    log(f"écrit : {ARTICLES_PATH}")


# ---------------------------------------------------------------- self-test


FIXTURE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
<item>
  <title>A Saint-Nazaire, les chantiers navals face au mur social</title>
  <link>https://www.liberation.fr/economie/exemple-1</link>
  <pubDate>{recent}</pubDate>
  <description><![CDATA[<p>Reportage sur les quais de Loire-Atlantique.</p>]]></description>
  <category>Économie</category><category>Saint-Nazaire</category>
</item>
<item>
  <title>Trois tours de scrutin et toujours pas de majorité</title>
  <link>https://www.liberation.fr/politique/exemple-2</link>
  <pubDate>{recent}</pubDate>
  <description>Analyse du blocage parlementaire.</description>
  <category>Politique</category>
</item>
<item>
  <title>Au large de Mayotte, la crise des kwassa-kwassa</title>
  <link>https://www.liberation.fr/societe/exemple-3</link>
  <pubDate>{old}</pubDate>
  <description>Trop vieux : doit être purgé.</description>
  <category>Mayotte</category>
</item>
</channel></rss>"""


def self_test():
    recent = datetime.now(timezone.utc) - timedelta(days=3)
    old = datetime.now(timezone.utc) - timedelta(days=120)
    xml = FIXTURE_RSS.format(
        recent=recent.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        old=old.strftime("%a, %d %b %Y %H:%M:%S +0000"),
    ).encode()

    items = parse_feed(xml)
    assert len(items) == 3, f"attendu 3 items, obtenu {len(items)}"

    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    fresh = [i for i in items if i["date"] and i["date"] >= cutoff]
    assert len(fresh) == 2, "la purge par date doit écarter l'item ancien"

    e1, w1 = match_place(items[0])
    assert e1 and e1["name"] == "Saint-Nazaire" and w1 == "tags", (e1, w1)

    e2, w2 = match_place(items[1])
    assert e2 is None, f"'Tours' (ambigu, hors tags) ne doit PAS matcher : {e2}"

    e3, _ = match_place(items[2])
    assert e3 and e3["name"] == "Mayotte"

    # le titre 1 contient aussi 'Loire-Atlantique' dans le chapô :
    # priorité aux tags, vérifions le fallback texte
    no_tags = dict(items[0], tags=[])
    e4, w4 = match_place(no_tags)
    assert e4 and w4 in ("titre", "chapô"), (e4, w4)

    print("self-test OK — parsing, fenêtre 62 j, matching géo (tags > texte, "
          "ambigus exclus du texte) : tout passe.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--no-paywall-filter", dest="paywall_filter",
                   action="store_false",
                   help="garde aussi les articles gratuits")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        self_test()
        sys.exit(0)
    collect(args)
