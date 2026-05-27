"""
more-podcast-intelligence / scraper.py
Scrapes top podcast charts from Spotify, YouTube, and Podcast Index.
Saves results to podcast_data.json for use by send_report.py.
"""

import json
import os
import time
import re
import hashlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ─────────────────────────────────────────────
# iHEART IDENTIFIERS — full master list
# ─────────────────────────────────────────────

PARENT_IDENTIFIERS = [
    "iheartmedia", "iheartradio", "iheartpodcasts",
    "iheart podcasts", "iheart media",
]

OWNED_NETWORKS = [
    "howstuffworks", "big money players", "black effect", "my cultura",
    "will media", "ruby media", "cool zone media", "tenderfoot tv",
    "pushkin industries", "exactly right", "shondaland", "shondaland audio",
    "meateater", "outspoken", "inflection",
]

HOWSTUFFWORKS_SHOWS = [
    "stuff you should know", "stuff you missed in history",
    "stuff they don't want you to know", "stuff mom never told you",
    "stuff to blow your mind", "brainstuff", "sciencestuff", "savor",
]

COOL_ZONE_SHOWS = [
    "behind the bastards", "it could happen here", "internet hate machine",
    "ghost church", "sixteenth minute",
]

TENDERFOOT_SHOWS = [
    "atlanta monster", "monster: dc sniper", "up and vanished",
    "your own backyard", "happy face", "hell and gone", "le monstre",
]

EXACTLY_RIGHT_SHOWS = [
    "my favorite murder", "buried bones", "that's messed up", "small town dicks",
]

BIG_MONEY_PLAYERS_SHOWS = [
    "all the smoke", "club shay shay", "shannon sharpe",
    "literally with rob lowe", "this is important", "fly on the wall",
    "good fortune with ed helms", "i am all in", "fake doctors real friends",
    "dear chelsea", "dear chelsea with chelsea handler",
]

BLACK_EFFECT_SHOWS = [
    "all the smoke", "85 south show", "the 85 south comedy show",
    "earn your leisure", "the black effect", "therapy for black girls",
    "the read", "yo, is this racist", "the lover boys",
    "questlove supreme", "the questlove show",
    "higher learning with van lathan", "say race with dr ibram x kendi",
    "in black america", "codie with an ie",
    "selective ignorance with mandii b", "selective ignorance",
    "laugh and learn", "i didn't know maybe you didn't either", "the trap",
]

MY_CULTURA_SHOWS = [
    "ponle pausa", "lele pons", "this is your life", "latinos who lunch",
    "brown girl self care", "my curious familia", "señora sex ed",
    "bleep with ana navarro", "who made you with eva longoria", "who made you",
    "locatora radio", "latinx files", "fierce",
]

SHONDALAND_SHOWS = [
    "shondaland audio", "katie's crib", "katie couric",
    "tell me with katie couric", "the betches", "betches",
    "you're wrong about", "scandal rewatch podcast", "greys anatomy rewatch",
    "how to save a planet", "bridgerton: the official podcast",
    "inventing anna", "queen charlotte",
]

PUSHKIN_SHOWS = [
    "revisionist history", "revisionist history with malcolm gladwell",
    "malcolm gladwell", "broken record", "broken record with rick rubin",
    "rick rubin", "cautionary tales", "tim harford", "against the rules",
    "michael lewis", "deep background with noah feldman", "the happiness lab",
    "dr laurie santos", "laurie santos", "the moment with brian koppelman",
    "rework", "by the book", "an arm and a leg", "poog", "land of the giants",
    "heavyweight", "not lost", "deep cover",
]

SPORTS_SHOWS = [
    "new heights with jason and travis kelce", "new heights",
    "jason kelce", "travis kelce",
    "the colin cowherd podcast", "colin cowherd",
    "the herd with colin cowherd", "the herd",
    "undisputed", "skip bayless", "shannon sharpe", "club shay shay",
    "the rich eisen show", "rich eisen", "rex chapman show",
    "pat mcafee show", "pat mcafee", "dan patrick show", "dan patrick",
    "mcafee and hawk", "bleacher report podcast", "the volume",
    "the rennae stubbs tennis podcast", "rennae stubbs",
    "women's sports audio network",
]

RADIO_PERSONALITY_SHOWS = [
    "the breakfast club", "charlamagne tha god", "dj envy", "jess hilarious",
    "bobby bones", "the bobby bones show",
    "bobby bones presents the bobbycast", "bobbycast",
    "ryan seacrest", "on air with ryan seacrest",
    "coast to coast am", "george noory",
    "armstrong and getty", "the armstrong and getty show",
    "the morning mash up", "brooke and jeffrey",
    "catch up with brandi cyrus", "brandi cyrus",
    "people every day", "steve harvey morning show",
    "the steve harvey morning show", "elvis duran",
]

NEWS_SHOWS = [
    "the daily dive", "politics war room",
    "the sean hannity podcast", "sean hannity",
    "the glen beck program", "glenn beck",
    "rush limbaugh", "the rush limbaugh show",
    "ben shapiro", "the ben shapiro show",
    "mark levin", "the mark levin show",
    "verdict with ted cruz", "ted cruz",
    "american history tellers", "american scandal",
    "the big picture", "inflection with andrea mitchell",
    "the clay travis and buck sexton show", "2 pros and a cup of joe",
    "breaking points with krystal and saagar",
    "countdown with keith olbermann",
    "next question with katie couric",
]

HEALTH_SHOWS = [
    "on purpose with jay shetty", "on purpose", "jay shetty",
    "iweigh with jameela jamil", "jameela jamil",
    "therapy for black girls", "the dr john delony show", "john delony",
    "a healthier mind", "the psychology of your 20s", "psychology of your 20s",
    "feel better live more", "ten percent happier",
    "ten percent happier with dan harris",
    "unlocking us with brene brown", "brene brown", "brené brown",
]

TRUE_CRIME_SHOWS = [
    "crime junkie", "dr death", "dr. death", "dirty john",
    "over my dead body", "blood ties", "even the rich",
    "betrayal", "betrayal podcast", "your own backyard",
    "scam goddess", "the cold", "something was wrong",
    "fighting conviction", "the piketon massacre", "atlanta monster",
    "dead eyes", "freeway phantom",
    "wrongful conviction", "wrongful conviction with jason flom", "jason flom",
    "redhanded", "disgraceland", "smokescreen", "school of humans",
    "american shadows", "the secret world of roald dahl",
    "love trapped", "doubt", "mind games",
]

COMEDY_SHOWS = [
    "las culturistas", "las culturistas with matt rogers and bowen yang",
    "matt rogers", "bowen yang",
    "fly on the wall", "fly on the wall with dana carvey",
    "dana carvey", "david spade",
    "this is important", "workaholics",
    "adam devine", "anders holm", "blake anderson",
    "smartless", "thanks dad", "ego nwodim",
    "good one a podcast about jokes", "good one",
    "conan o'brien needs a friend", "conan obrien needs a friend",
    "conan needs a friend", "handsome rambler",
    "the ron burgundy podcast", "snafu with ed helms",
    "here's the thing with alec baldwin", "boysober", "ok storytime",
]

CULTURE_SHOWS = [
    "bookmarked by reese's book club", "bookmarked", "reese witherspoon",
    "the michelle obama podcast", "michelle obama",
    "oprah's supersoul", "oprah",
    "getting curious with jonathan van ness", "jonathan van ness", "jvn",
    "ologies with alie ward", "ologies",
    "no stupid questions", "freakonomics radio", "freakonomics", "stephen dubner",
    "stuff you should know", "a way with words", "wait wait don't tell me",
    "drink champs", "red table talk", "two ts in a pod", "pod meets world",
    "brown ambition", "good game with sarah spain",
    "latino usa", "radio ambulante", "american history hotline", "hungry for history",
    "the official yellowstone podcast", "no grip", "earn your leisure",
]

NETFLIX_PARTNERSHIP_SHOWS = [
    "my favorite murder", "the breakfast club",
    "bobby bones presents the bobbycast",
    "behind the bastards", "the psychology of your 20s",
    "dear chelsea", "this is important", "las culturistas",
    "new heights", "fly on the wall", "literally with rob lowe",
    "the questlove show", "earn your leisure", "smartless",
]

BLOOMBERG_SHOWS = [
    "odd lots", "masters in business", "bloomberg surveillance",
    "bloomberg businessweek", "trillions", "bloomberg crypto",
    "zero", "money stuff the podcast", "foundering",
    "the david rubenstein show",
]

MEATEATER_SHOWS = [
    "meateater podcast", "the meateater podcast", "steven rinella", "rinella",
    "wired to hunt", "out alive", "hunting collective", "hunting with style",
    "bear grease", "cal of the wild", "in pursuit", "meateater kids",
]

IHEARTMEDIA_HOSTS = [
    "charlamagne tha god", "dj envy", "jess hilarious", "bobby bones",
    "colin cowherd", "jay shetty", "karen kilgariff", "georgia hardstark",
    "robert evans", "payne lindsey", "donald albright",
    "malcolm gladwell", "josh clark", "chuck bryant",
    "christian johnson", "will pearson",
    "katie couric", "jameela jamil", "chelsea handler",
    "rob lowe", "ed helms", "dana carvey",
    "matt rogers", "bowen yang", "shonda rhimes", "questlove",
    "jason kelce", "travis kelce", "rich eisen",
    "ana navarro", "eva longoria", "ego nwodim",
    "brene brown", "brené brown", "reese witherspoon",
]

IHEART_IDENTIFIERS = list(set(
    PARENT_IDENTIFIERS + OWNED_NETWORKS + HOWSTUFFWORKS_SHOWS +
    COOL_ZONE_SHOWS + TENDERFOOT_SHOWS + EXACTLY_RIGHT_SHOWS +
    BIG_MONEY_PLAYERS_SHOWS + BLACK_EFFECT_SHOWS + MY_CULTURA_SHOWS +
    SHONDALAND_SHOWS + PUSHKIN_SHOWS + SPORTS_SHOWS +
    RADIO_PERSONALITY_SHOWS + NEWS_SHOWS + HEALTH_SHOWS +
    TRUE_CRIME_SHOWS + COMEDY_SHOWS + CULTURE_SHOWS +
    NETFLIX_PARTNERSHIP_SHOWS + BLOOMBERG_SHOWS + MEATEATER_SHOWS +
    IHEARTMEDIA_HOSTS
))


def is_iheart(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in IHEART_IDENTIFIERS)


def check_iheart(*fields) -> bool:
    return any(is_iheart(f) for f in fields)


# ─────────────────────────────────────────────
# SPOTIFY
# Auth: OAuth client_credentials
# Sections: Top 5 Shows + Editors Pick
# ─────────────────────────────────────────────

def get_spotify_token() -> str:
    client_id     = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=15,
    )
    if r.status_code != 200:
        raise Exception(f"Spotify auth failed: {r.text}")
    return r.json()["access_token"]


def scrape_spotify():
    print("\n🟢 Scraping Spotify...")
    results = {"editors_pick": [], "top_shows": []}

    try:
        token   = get_spotify_token()
        headers = {"Authorization": f"Bearer {token}"}

        # ── Top Shows: search for top US podcasts by category ──
        # Spotify API doesn't have a direct "top charts" endpoint,
        # so we query the most popular shows across key categories
        top_shows = []
        seen = set()

        categories = [
            ("true crime",    "True Crime"),
            ("news",          "News"),
            ("comedy",        "Comedy"),
            ("society",       "Society & Culture"),
            ("business",      "Business"),
        ]

        for query, _ in categories:
            r = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params={
                    "q":      query,
                    "type":   "show",
                    "market": "US",
                    "limit":  3,
                },
                timeout=15,
            )
            if r.status_code != 200:
                continue
            shows = r.json().get("shows", {}).get("items", [])
            for show in shows:
                if not show:
                    continue
                title = show.get("name", "")
                if title and title not in seen:
                    seen.add(title)
                    top_shows.append({
                        "title":  title,
                        "author": show.get("publisher", ""),
                        "image":  (show.get("images") or [{}])[0].get("url", ""),
                        "url":    show.get("external_urls", {}).get("spotify", ""),
                        "iheart": check_iheart(title, show.get("publisher", "")),
                    })
                if len(top_shows) >= 5:
                    break
            if len(top_shows) >= 5:
                break
            time.sleep(0.3)

        for i, show in enumerate(top_shows[:5], 1):
            show["rank"] = i
        results["top_shows"] = top_shows[:5]
        print(f"  ✅ Spotify top shows: {len(results['top_shows'])}")

        # ── Editors Pick: featured/editorial shows ──
        editors = []
        seen_ep = set()

        editorial_queries = [
            "editors pick podcast 2025",
            "best new podcast",
            "featured podcast spotlight",
        ]

        for query in editorial_queries:
            r = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params={
                    "q":      query,
                    "type":   "show",
                    "market": "US",
                    "limit":  4,
                },
                timeout=15,
            )
            if r.status_code != 200:
                continue
            shows = r.json().get("shows", {}).get("items", [])
            for show in shows:
                if not show:
                    continue
                title = show.get("name", "")
                if title and title not in seen_ep and title not in seen:
                    seen_ep.add(title)
                    editors.append({
                        "title":  title,
                        "author": show.get("publisher", ""),
                        "image":  (show.get("images") or [{}])[0].get("url", ""),
                        "url":    show.get("external_urls", {}).get("spotify", ""),
                        "iheart": check_iheart(title, show.get("publisher", "")),
                    })
            if len(editors) >= 6:
                break
            time.sleep(0.3)

        results["editors_pick"] = editors[:6]
        print(f"  ✅ Spotify editors pick: {len(results['editors_pick'])}")

    except Exception as e:
        print(f"  ⚠️ Spotify failed: {e}")

    return results


# ─────────────────────────────────────────────
# YOUTUBE
# Source: charts.youtube.com/podcasts
# Section: Top 10 Shows (weekly by watchtime)
# ─────────────────────────────────────────────

def scrape_youtube():
    print("\n🔴 Scraping YouTube...")
    results = {"top_shows": []}

    try:
        chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        if not chromium_path:
            for p in ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]:
                import shutil
                if shutil.which(p.split("/")[-1]):
                    chromium_path = p
                    break
        launch_kwargs = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path

        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://charts.youtube.com/podcasts", timeout=45000)
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all(
            lambda t: t.name in ["ytmc-entry-row", "div", "li"] and
            any(cls in " ".join(t.get("class", []))
                for cls in ["entry-row", "chart-entry", "ytChartEntry",
                            "EntityRowRenderer", "MusicResponsiveListItemRenderer"])
        )

        seen = set()
        for row in rows:
            title_el = row.find(
                ["yt-formatted-string", "span", "h3", "h2", "a"],
                class_=re.compile(r"title|name|podcast", re.I)
            )
            if not title_el:
                title_el = row.find(["h3", "h2", "strong"])
            title  = title_el.get_text(strip=True) if title_el else ""
            img_el = row.find("img")
            img    = img_el.get("src", "") if img_el else ""
            link   = row.find("a")
            href   = link.get("href", "") if link else ""
            if href and not href.startswith("http"):
                href = "https://www.youtube.com" + href

            if title and title not in seen and len(title) > 2:
                seen.add(title)
                results["top_shows"].append({
                    "rank":   len(results["top_shows"]) + 1,
                    "title":  title,
                    "author": "",
                    "image":  img,
                    "url":    href,
                    "iheart": check_iheart(title),
                })
            if len(results["top_shows"]) >= 10:
                break

        # Fallback: try embedded JSON
        if len(results["top_shows"]) < 3:
            scripts = soup.find_all("script")
            for script in scripts:
                content = script.string or ""
                if "podcastTitle" in content or "chartEntry" in content:
                    try:
                        matches = re.findall(r'\{[^{}]*"title"[^{}]*\}', content)
                        for m in matches[:10]:
                            try:
                                obj   = json.loads(m)
                                title = obj.get("title", obj.get("podcastTitle", ""))
                                if title and title not in seen:
                                    seen.add(title)
                                    results["top_shows"].append({
                                        "rank":   len(results["top_shows"]) + 1,
                                        "title":  title,
                                        "author": obj.get("channelName", ""),
                                        "image":  obj.get("thumbnail", ""),
                                        "url":    obj.get("url", ""),
                                        "iheart": check_iheart(title),
                                    })
                            except Exception:
                                pass
                    except Exception:
                        pass

        print(f"  ✅ YouTube top shows: {len(results['top_shows'])}")

    except Exception as e:
        print(f"  ⚠️ YouTube failed: {e}")

    return results


# ─────────────────────────────────────────────
# PODCAST INDEX
# Auth: HMAC-SHA1 (key + secret + timestamp)
# Section: Top 10 Trending (same layout as YouTube)
# ─────────────────────────────────────────────

def scrape_podcast_index():
    print("\n🎙️  Scraping Podcast Index...")
    results = {"top_shows": []}

    try:
        api_key    = os.environ["PODCASTINDEX_KEY"]
        api_secret = os.environ["PODCASTINDEX_SECRET"]
        epoch      = str(int(time.time()))
        sha1       = hashlib.sha1(
            (api_key + api_secret + epoch).encode()
        ).hexdigest()

        headers = {
            "X-Auth-Date":  epoch,
            "X-Auth-Key":   api_key,
            "Authorization": sha1,
            "User-Agent":   "MorePodcastIntelligence/1.0",
        }

        r = requests.get(
            "https://api.podcastindex.org/api/1.0/podcasts/trending",
            headers=headers,
            params={
                "max":    10,
                "lang":   "en",
                "since":  -604800,   # last 7 days
            },
            timeout=15,
        )

        if r.status_code != 200:
            raise Exception(f"Status {r.status_code}: {r.text[:200]}")

        feeds = r.json().get("feeds", [])

        for i, feed in enumerate(feeds[:10], 1):
            title  = feed.get("title", "")
            author = feed.get("author", feed.get("ownerName", ""))
            img    = feed.get("image", feed.get("artwork", ""))
            url    = feed.get("link", "")
            desc   = feed.get("description", "")
            results["top_shows"].append({
                "rank":   i,
                "title":  title,
                "author": author,
                "image":  img,
                "url":    url,
                "iheart": check_iheart(title, author, desc),
            })

        print(f"  ✅ Podcast Index trending: {len(results['top_shows'])}")

    except Exception as e:
        print(f"  ⚠️ Podcast Index failed: {e}")

    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🎙️  More Podcast Intelligence Scraper")
    print(f"📅  {today}")
    print("=" * 50)

    data = {
        "date":           today,
        "spotify":        scrape_spotify(),
        "youtube":        scrape_youtube(),
        "podcast_index":  scrape_podcast_index(),
    }

    with open("podcast_data.json", "w") as f:
        json.dump(data, f, indent=2)

    print("\n📊 Summary:")
    print(f"  Spotify       — editors pick: {len(data['spotify']['editors_pick'])} | top shows: {len(data['spotify']['top_shows'])}")
    print(f"  YouTube       — top shows: {len(data['youtube']['top_shows'])}")
    print(f"  Podcast Index — trending: {len(data['podcast_index']['top_shows'])}")

    all_shows = (
        data["spotify"]["editors_pick"] +
        data["spotify"]["top_shows"] +
        data["youtube"]["top_shows"] +
        data["podcast_index"]["top_shows"]
    )
    iheart_hits = [s for s in all_shows if s.get("iheart")]
    if iheart_hits:
        print(f"\n🚨 iHeart shows detected ({len(iheart_hits)}):")
        for s in iheart_hits:
            print(f"   → {s['title']}")
    else:
        print("\n  ℹ️  No iHeart shows detected this run")

    print("\n✅ Data saved to podcast_data.json")