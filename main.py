import requests
import argparse
from urllib.parse import urljoin
import re
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from io import BytesIO
import gzip

# Initialize colorama
init()

# Define the User-Agent string for Google Chrome
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def print_header(text):
    print(f"{Fore.CYAN}[i] {Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}[+] {Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}[!] {Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}[-] {Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_header_table(headers):
    print_header("HTTP Headers:")
    print(f"{Fore.WHITE}{Style.BRIGHT}{'Name':<30} {'Value':<70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-' * 30} { '-' * 70}{Style.RESET_ALL}")
    for header, value in headers.items():
        print(f"{Fore.MAGENTA}{header:<30} {Fore.WHITE}{value:<70}{Style.RESET_ALL}")

def get_headers(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        headers = response.headers
        print_header(f"Headers for {url}:")
        print_header_table(headers)
    except requests.exceptions.RequestException as e:
        print_error(f"Error fetching {url}: {e}")

def check_file(url, filename):
    file_url = urljoin(url, filename)
    try:
        response = requests.get(file_url, headers={"User-Agent": USER_AGENT})
        if response.status_code == 200:
            print_success(f"'{filename}' found at: {file_url}")
        else:
            print_warning(f"'{filename}' not found at: {file_url}")
    except requests.exceptions.RequestException as e:
        print_error(f"Error fetching {file_url}: {e}")

def get_wordpress_version(content):
    # Busca en el contenido un meta tag o comentario que indique la versión de WordPress
    version = re.search(r'wordpress.org/\?v=([0-9\.]+)', content)
    if version:
        return version.group(1)
    else:
        return None

def decompress_content(content):
    buf = BytesIO(content)
    f = gzip.GzipFile(fileobj=buf)
    return f.read().decode('utf-8')

def check_feeds(url):
    feeds = [
        "feed",
        "index.php/feed",
        "index.php/comments/feed",
        "comments/feed"
    ]
    found_any_feed = False
    for feed_path in feeds:
        feed_url = urljoin(url, feed_path)
        try:
            response = requests.get(feed_url, headers={"User-Agent": USER_AGENT})
            if response.status_code == 200:
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    content = decompress_content(response.content)
                else:
                    content = response.text
                version = get_wordpress_version(content)
                if version:
                    print_success(f"WordPress version detected from {feed_path}: {version}")
                else:
                    print_error(f"WordPress version not found in {feed_path}.")
                found_any_feed = True
        except requests.exceptions.RequestException as e:
            print_error(f"Error fetching {feed_url}: {e}")
    
    if not found_any_feed:
        print_warning("No WordPress feeds found.")

def get_source(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecuta Chrome en modo sin cabeza
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)

    # Obtén el contenido de la página después de que se haya cargado completamente
    html = driver.page_source
    driver.quit()
    return html


def detect_theme_selenium(html):
    print_header("Detecting WordPress theme via Selenium:")
    # Busca los temas en el HTML
    css_files = re.findall(r'<link[^>]+href="([^"]+)"', html)
    theme_found = False
    for css_file in css_files:
        if '/wp-content/themes/' in css_file:
            theme_match = re.search(r'/wp-content/themes/([a-zA-Z0-9-_]+)/', css_file)
            if theme_match:
                theme_name = theme_match.group(1)
                print_success(f"WordPress theme detected: {theme_name}")
                theme_found = True
                break
    if not theme_found:
        print_error("WordPress theme not found in the HTML.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and display HTTP headers from a given URL and check for specific WordPress files.")
    parser.add_argument("-u", "--url", type=str, required=True, help="The URL to analyze.")
    parser.add_argument("--selenium", action='store_true', help="Use Selenium to detect theme")

    args = parser.parse_args()

    html = get_source(args.url)
    

    # Fetch and display headers
    get_headers(args.url)
    
    # Check if readme.html exists
    check_file(args.url, "readme.html")
    
    # Check if wp-cron.php exists
    check_file(args.url, "wp-cron.php")

    # Check WordPress feeds
    check_feeds(args.url)
    
    # Detect WordPress theme
    detect_theme_selenium(html)
