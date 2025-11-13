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
from unidecode import unidecode 

# -------- Configuration --------
ROOT_DIR = pathlib.Path("Learning/French/Larousse")
BASE_URL = "https://www.larousse.fr"

# --- Helper Functions ---

def ensure_paths(word: str):
    """Sets up the directory structure for the word."""
    word_dir = ROOT_DIR / word
    # Only the folders present in your original working version
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

# --- MODIFIED: Added 'direction' argument and fixed typo ---
def build_url(word_or_url: str, direction: str) -> str:
    """Builds the full Larousse URL from a word or URL, using the specified dictionary direction."""
    if word_or_url.startswith("http"):
        return word_or_url
    # CORRECTED to use the dynamic 'direction' variable
    return f"{BASE_URL}/dictionnaires/{direction}/{word_or_url}" 
# --- END MODIFIED ---

def download_asset(url: str, out_path: pathlib.Path) -> bool:
    """Downloads a single asset (CSS, JS, audio) to a specific path."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        # Suppress "404" warnings for cleaner output
        if "404" not in str(e):
            print(f"[warn] Failed to download {url}: {e}")
        return False

def get_local_path(url: str, asset_dir: pathlib.Path, prefix: str = "", idx: int = 0) -> pathlib.Path:
    """Creates a predictable local file path for a downloaded asset."""
    try:
        # Strip query parameters (like ?v=123) from filename
        parsed_path = urlparse(url).path
        parsed_name_with_query = pathlib.Path(parsed_path).name 
        parsed_name = parsed_name_with_query.split('?')[0].split('#')[0] 

        if not parsed_name or len(parsed_name) > 100: 
             ext_map = { 'css': '.css', 'js': '.js', 'audio': '.mp3' }
             ext = ext_map.get(asset_dir.name, '.asset')
             parsed_name = f"{prefix}_{idx}{ext}"

        # Special handling for audio to ensure .mp3 extension
        if asset_dir.name == 'audio':
             name_no_ext, _ = os.path.splitext(parsed_name)
             parsed_name = f"{name_no_ext}.mp3"

        return asset_dir / parsed_name
    except Exception:
        return asset_dir / f"{prefix}_{idx}.asset"

# --- Core Scraping Logic (Updated) ---

# --- MODIFIED: Added 'direction' argument ---
def scrape_larousse(word_or_url: str, direction: str):
    """
    Scrapes the Larousse entry, preserving original HTML structure
    and rewriting asset links to be local.
    """
    
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
    
    # 4. Use the original 'word_or_url' and direction to build the fetch URL
    url = build_url(word_or_url, direction) # Passed direction here
    
    print(f"[info] Scraping '{raw_word}' from {url}")
    print(f"[info] Saving to directory: {word_dir}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Increase timeout for complex pages
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
    
    # Asset downloading logic (from the user's working version)
    
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
    audio_links = []
    
    for idx, audio in enumerate(article.find_all('audio')): 
        if audio.get('src'):
            orig_src = absolute_url(audio['src'])
            local_path = get_local_path(orig_src, audio_dir, word, idx)
            
            if download_asset(orig_src, local_path):
                audio_files_found += 1
                audio_links.append(os.path.relpath(local_path, word_dir))
            
            # Remove the original <audio> element as it is useless without Larousse's JS
            audio.decompose()

    # --- HACK FIX: Replace speaker icons and create playable links ---
    print("[info] Replacing speaker icons with '▶️' links to local audio.")
    audio_index = 0
    for speaker_icon in article.find_all('span', class_='icon-speaker'):
        if audio_index < len(audio_links):
            # Create a direct link to the local MP3 file
            link_tag = soup.new_tag("a", href=audio_links[audio_index], target="_blank", title="Play Audio (Offline)")
            link_tag.string = '▶️' # The simple, universally available play symbol
            speaker_icon.replace_with(link_tag)
            audio_index += 1
        else:
            # If we run out of audio files, just replace the icon with a generic symbol
            speaker_icon.clear()
            speaker_icon.append('🔊')
    # --- END HACK FIX ---


    title = soup.find("title").string or f"Entry for {word}"
    
    final_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {os.linesep.join(str(link) for link in soup.head.find_all('link', rel='stylesheet'))}
    <style>
        body {{ margin: 24px; background: #fff; }}
        /* Ensure the play icon link is visible and clickable */
        a[href$=".mp3"] {{ text-decoration: none; font-size: 1.2em; color: inherit; margin-right: 5px; }} 
        /* Remove font-family that was causing strange symbols */
        span.icon-speaker {{ font-family: unset; }} 
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
    print(f"[done] Audio: {audio_files_found} file(s) - Playable via '▶️' link.")
    print(f"[done] CSS: {css_files_found} file(s)")
    print(f"[done] JS: {js_files_found} file(s)")
    print("-" * 30)
# --- END MODIFIED SCRAPING LOGIC ---

# -------- Simple Tkinter UI (Updated) --------

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

# --- MODIFIED: Added direction_var to arguments ---
def start_scrape_thread(entry_widget, direction_var):
    """Starts the scraping process in a separate thread"""
    url_or_word = entry_widget.get()
    direction = direction_var.get()
    
    if not url_or_word:
        print("[error] Please enter a word or URL.\n")
        return
    
    scrape_button.config(state="disabled")
    
    def scrape_task():
        try:
            # --- MODIFIED: Passed direction to scrape_larousse ---
            scrape_larousse(url_or_word, direction)
            # --- END MODIFIED ---
        except Exception as e:
            print(f"[error] An unexpected error occurred: {e}\n")
        finally:
            scrape_button.config(state="normal")
            
    thread = threading.Thread(target=scrape_task)
    thread.daemon = True 
    thread.start()

# --- Main Entry Point (Updated) ---

if __name__ == "__main__":
    print("Starting Scraper UI...")
    print("Please ensure you have run: pip install playwright beautifulsoup4 requests unidecode")
    print("And installed browsers: playwright install")
    print("-" * 30)
    
    root = tk.Tk()
    root.title("Larousse Scraper")
    root.geometry("650x450") 

    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.pack(fill="both", expand=True)

    input_frame = tk.Frame(main_frame)
    input_frame.pack(fill="x")

    tk.Label(input_frame, text="Word or URL:").pack(side="left", padx=(0, 5))
    
    url_entry = tk.Entry(input_frame, width=50)
    url_entry.pack(side="left", fill="x", expand=True)
    
    # --- NEW: Dictionary selection frame ---
    direction_frame = tk.Frame(main_frame)
    direction_frame.pack(fill="x", pady=5)
    
    tk.Label(direction_frame, text="Dictionary:").pack(side="left", padx=(0, 5))
    
    # Variable to hold the selected dictionary direction
    direction_var = tk.StringVar(value="francais-anglais")
    
    rb_fr_en = tk.Radiobutton(direction_frame, text="French -> English (francais-anglais)", 
                             variable=direction_var, value="francais-anglais")
    rb_fr_en.pack(side="left")
    
    rb_en_fr = tk.Radiobutton(direction_frame, text="English -> French (anglais-francais)", 
                             variable=direction_var, value="anglais-francais")
    rb_en_fr.pack(side="left", padx=10)
    
    scrape_button = tk.Button(input_frame, text="Scrape", 
                              command=lambda: start_scrape_thread(url_entry, direction_var))
    scrape_button.pack(side="left", padx=(5, 0))
    # --- END NEW ---

    tk.Label(main_frame, text="Log Output:", anchor="w").pack(fill="x", pady=(10, 5))
    
    console_output = scrolledtext.ScrolledText(main_frame, height=15, state='disabled')
    console_output.pack(fill="both", expand=True)

    sys.stdout = TextRedirector(console_output)
    sys.stderr = TextRedirector(console_output)

    print("Ready. Select dictionary, then enter a word (e.g., 'chat' or 'cat').")
    
    root.mainloop()