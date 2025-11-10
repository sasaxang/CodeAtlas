import os
import re
import sys
import pathlib
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# -------- Configuration --------
ROOT_DIR = pathlib.Path("Learning/French/Larousse")
BASE_URL = "https://www.larousse.fr"

def ensure_paths(word: str):
    """Sets up the directory structure for the word."""
    word_dir = ROOT_DIR / word
    audio_dir = word_dir / "audio"
    css_dir = word_dir / "css"
    js_dir = word_dir / "js"
    
    word_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)
    
    return word_dir, audio_dir, css_dir, js_dir

def normalize_space(text: str) -> str:
    """Cleans up whitespace in text."""
    return re.sub(r"\s+", " ", text).strip()

def absolute_url(path_or_url: str) -> str:
    """Ensures a URL is absolute."""
    return path_or_url if path_or_url.startswith("http") else urljoin(BASE_URL, path_or_url)

def build_url(word_or_url: str) -> str:
    """Builds the full Larousse URL from a word or URL."""
    return word_or_url if word_or_url.startswith("http") else f"{BASE_URL}/dictionnaires/francais-anglais/{word_or_url}"

def download_asset(url: str, out_path: pathlib.Path) -> bool:
    """Downloads a single asset (CSS, JS, audio) to a specific path."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"[warn] Failed to download {url}: {e}")
        return False

def get_local_path(url: str, asset_dir: pathlib.Path, prefix: str = "", idx: int = 0) -> pathlib.Path:
    """Creates a predictable local file path for a downloaded asset."""
    try:
        # Try to get the original filename
        parsed_name = pathlib.Path(urlparse(url).path).name
        if not parsed_name:
            # If no name, create one
            ext = ".css" if "css" in asset_dir.name else ".js" if "js" in asset_dir.name else ".mp3"
            parsed_name = f"{prefix}_{idx}{ext}"
        return asset_dir / parsed_name
    except Exception:
        # Fallback
        return asset_dir / f"{prefix}_{idx}.asset"

def scrape_larousse(word_or_url: str):
    """
    Scrapes the Larousse entry, preserving original HTML structure
    and rewriting asset links to be local.
    """
    word = pathlib.Path(word_or_url).stem
    word_dir, audio_dir, css_dir, js_dir = ensure_paths(word)
    url = build_url(word_or_url)
    
    print(f"[info] Scraping {word} from {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Increase timeout just in case
            page.goto(url, wait_until="networkidle", timeout=60000)
            html = page.content()
            browser.close()
    except Exception as e:
        print(f"[error] Playwright failed: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # --- Find the main article content ---
    article = soup.find("article", class_="article_bilingue") or \
              soup.find("div", class_="content fr-en") or \
              soup.find("article")

    if article is None:
        out_html = word_dir / f"{word}.html"
        out_html.write_text(
            f"<!DOCTYPE html><html><body><p>No article found for '{word_or_url}'.</p></body></html>",
            encoding="utf-8",
        )
        print(f"[info] No article found. Wrote placeholder: {out_html}")
        return

    # --- 1. Process CSS files ---
    print("[info] Downloading CSS...")
    css_files_found = 0
    for idx, link in enumerate(soup.find_all('link', rel='stylesheet')):
        if link.get('href'):
            orig_href = absolute_url(link['href'])
            local_path = get_local_path(orig_href, css_dir, "style", idx)
            if download_asset(orig_href, local_path):
                # Rewrite the link to point to the local file
                link['href'] = os.path.relpath(local_path, word_dir)
                css_files_found += 1
    
    # --- 2. Process JS files ---
    print("[info] Downloading JS...")
    js_files_found = 0
    for idx, script in enumerate(soup.find_all('script')):
        if script.get('src'):
            orig_src = absolute_url(script['src'])
            local_path = get_local_path(orig_src, js_dir, "script", idx)
            if download_asset(orig_src, local_path):
                # Rewrite the link to point to the local file
                script['src'] = os.path.relpath(local_path, word_dir)
                js_files_found += 1
    
    # --- 3. Process Audio files ---
    print("[info] Downloading Audio...")
    audio_files_found = 0
    for idx, audio in enumerate(soup.find_all('audio')):
        if audio.get('src'):
            orig_src = absolute_url(audio['src'])
            local_path = get_local_path(orig_src, audio_dir, word, idx)
            if download_asset(orig_src, local_path):
                # Rewrite the link to point to the local file
                audio['src'] = os.path.relpath(local_path, word_dir)
                audio_files_found += 1

    # --- 4. Create Final HTML ---
    # We create a new, clean HTML document containing just the
    # downloaded assets in the <head> and the isolated <article>
    # in the <body>. This removes all the extra site navigation, ads, etc.
    
    title = soup.find("title").string or f"Entry for {word}"
    
    final_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {os.linesep.join(str(link) for link in soup.head.find_all('link', rel='stylesheet'))}
  <style>
    /* Add simple body margin for better viewing */
    body {{ margin: 24px; }}
  </style>
</head>
<body>
  {str(article)}
  
  {os.linesep.join(str(script) for script in soup.find_all('script') if script.get('src'))}
</body>
</html>"""

    out_html = word_dir / f"{word}.html"
    out_html.write_text(final_html, encoding="utf-8")

    print(f"\n[done] Saved: {out_html}")
    print(f"[done] Audio: {audio_files_found} file(s) in {audio_dir}")
    print(f"[done] CSS: {css_files_found} file(s) in {css_dir}")
    print(f"[done] JS: {js_files_found} file(s) in {js_dir}")


# -------- Entry point --------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python larousse_scraper.py <word_or_url>")
        print("Example: python larousse_scraper.py chat")
        print("Example: python larousse_scraper.py https://www.larousse.fr/dictionnaires/francais-anglais/chat/14765")
        sys.exit(1)
    
    # Ensure dependencies are installed
    print("Please ensure you have run: pip install playwright beautifulsoup4 requests")
    print("And installed browsers: playwright install")
    
    scrape_larousse(sys.argv[1])