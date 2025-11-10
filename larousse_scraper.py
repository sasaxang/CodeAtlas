import os
import re
import sys
import pathlib
import requests
import threading
import tkinter as tk
from tkinter import scrolledtext
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from unidecode import unidecode # <-- NEW IMPORT

# -------- Configuration --------
ROOT_DIR = pathlib.Path("Learning/French/Larousse")
BASE_URL = "https://www.larousse.fr"

# --- Helper Functions (No changes) ---

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
        parsed_name = pathlib.Path(urlparse(url).path).name
        if not parsed_name or len(parsed_name) > 100: 
             ext_map = { 'css': '.css', 'js': '.js', 'audio': '.mp3' }
             ext = ext_map.get(asset_dir.name, '.asset')
             parsed_name = f"{prefix}_{idx}{ext}"
        return asset_dir / parsed_name
    except Exception:
        return asset_dir / f"{prefix}_{idx}.asset"

# --- Core Scraping Logic (Updated) ---

def scrape_larousse(word_or_url: str):
    """
    Scrapes the Larousse entry, preserving original HTML structure
    and rewriting asset links to be local.
    """
    
    # --- NEW: Sanitize the word for file paths ---
    # 1. Get the original word (stem)
    if word_or_url.startswith("http"):
        raw_word = pathlib.Path(urlparse(word_or_url).path).stem
    else:
        raw_word = word_or_url
        
    if not raw_word:
        raw_word = "entry"
    
    # 2. Create a "sanitized" version for file/directory names
    word = unidecode(raw_word)
    
    # 3. Use the sanitized 'word' for paths
    word_dir, audio_dir, css_dir, js_dir = ensure_paths(word)
    
    # 4. Use the original 'word_or_url' to build the fetch URL
    url = build_url(word_or_url)
    
    print(f"[info] Scraping '{raw_word}' from {url}")
    print(f"[info] Saving to directory: {word_dir}")
    # --- End of sanitation changes ---

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            html = page.content()
            browser.close()
    except Exception as e:
        print(f"[error] Playwright failed: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    article = soup.find("article", class_="article_bilingue") or \
              soup.find("div", class_="content fr-en") or \
              soup.find("article")

    if article is None:
        print(f"[info] No article found for '{word_or_url}'.")
        return

    print("[info] Removing internal links...")
    for a_tag in article.find_all('a'):
        a_tag.name = "span" 
        if a_tag.has_attr('href'):
            del a_tag['href']
        if a_tag.has_attr('target'):
            del a_tag['target']
    
    print("[info] Downloading CSS...")
    css_files_found = 0
    for idx, link in enumerate(soup.find_all('link', rel='stylesheet')):
        if link.get('href'):
            orig_href = absolute_url(link['href'])
            local_path = get_local_path(orig_href, css_dir, "style", idx)
            
            if download_asset(orig_href, local_path):
                link['href'] = os.path.relpath(local_path, word_dir)
                css_files_found += 1
            else:
                link.decompose()
    
    print("[info] Downloading JS...")
    js_files_found = 0
    for idx, script in enumerate(soup.find_all('script')):
        if script.get('src'):
            orig_src = absolute_url(script['src'])
            local_path = get_local_path(orig_src, js_dir, "script", idx)
            
            if download_asset(orig_src, local_path):
                script['src'] = os.path.relpath(local_path, word_dir)
                js_files_found += 1
            else:
                script.decompose()
    
    print("[info] Downloading Audio...")
    audio_files_found = 0
    for idx, audio in enumerate(article.find_all('audio')): 
        if audio.get('src'):
            orig_src = absolute_url(audio['src'])
            local_path = get_local_path(orig_src, audio_dir, word, idx)
            
            if download_asset(orig_src, local_path):
                audio['src'] = os.path.relpath(local_path, word_dir)
                audio_files_found += 1
            else:
                audio.decompose()

    title = soup.find("title").string or f"Entry for {word}"
    
    final_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {os.linesep.join(str(link) for link in soup.head.find_all('link', rel='stylesheet'))}
  <style>
    body {{ margin: 24px; background: #fff; }}
  </style>
</head>
<body>
  {str(article)}
  {os.linesep.join(str(script) for script in soup.find_all('script') if script.get('src'))}
</body>
</html>"""

    # Use the sanitized 'word' for the output filename
    out_html = word_dir / f"{word}.html"
    out_html.write_text(final_html, encoding="utf-8")

    print(f"\n[done] Saved: {out_html}")
    print(f"[done] Audio: {audio_files_found} file(s)")
    print(f"[done] CSS: {css_files_found} file(s)")
    print(f"[done] JS: {js_files_found} file(s)")
    print("-" * 30)

# -------- Simple Tkinter UI (No changes) --------

class TextRedirector:
    """Redirects stdout to a tkinter Text widget"""
    def __init__(self, widget):
        self.widget = widget

    def write(self, s):
        self.widget.configure(state='normal')
        self.widget.insert('end', s)
        self.widget.see('end')
        self.widget.configure(state='disabled')

    def flush(self):
        pass 

def start_scrape_thread(entry_widget):
    """Starts the scraping process in a separate thread"""
    url_or_word = entry_widget.get()
    if not url_or_word:
        print("[error] Please enter a word or URL.\n")
        return
    
    scrape_button.config(state="disabled")
    
    def scrape_task():
        try:
            scrape_larousse(url_or_word)
        except Exception as e:
            print(f"[error] An unexpected error occurred: {e}\n")
        finally:
            scrape_button.config(state="normal")
            
    thread = threading.Thread(target=scrape_task)
    thread.daemon = True 
    thread.start()

# --- Main Entry Point ---

if __name__ == "__main__":
    print("Starting Scraper UI...")
    print("Please ensure you have run: pip install playwright beautifulsoup4 requests unidecode")
    print("And installed browsers: playwright install")
    print("-" * 30)
    
    root = tk.Tk()
    root.title("Larousse Scraper")
    root.geometry("600x400")

    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.pack(fill="both", expand=True)

    input_frame = tk.Frame(main_frame)
    input_frame.pack(fill="x")

    tk.Label(input_frame, text="Word or URL:").pack(side="left", padx=(0, 5))
    
    url_entry = tk.Entry(input_frame, width=50)
    url_entry.pack(side="left", fill="x", expand=True)

    scrape_button = tk.Button(input_frame, text="Scrape", 
                              command=lambda: start_scrape_thread(url_entry))
    scrape_button.pack(side="left", padx=(5, 0))

    tk.Label(main_frame, text="Log Output:", anchor="w").pack(fill="x", pady=(10, 5))
    
    console_output = scrolledtext.ScrolledText(main_frame, height=15, state='disabled')
    console_output.pack(fill="both", expand=True)

    sys.stdout = TextRedirector(console_output)
    sys.stderr = TextRedirector(console_output)

    print("Ready. Enter a word (e.g., 'chat') or a full URL.")
    
    root.mainloop()