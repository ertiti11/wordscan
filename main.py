import requests
import argparse
from urllib.parse import urljoin
import re

# Define the User-Agent string for Google Chrome
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def get_headers(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        headers = response.headers
        print(f"Headers for {url}:")
        for header, value in headers.items():
            print(f"{header}: {value}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")

def check_file(url, filename):
    file_url = urljoin(url, filename)
    try:
        response = requests.get(file_url, headers={"User-Agent": USER_AGENT})
        if response.status_code == 200:
            print(f"'{filename}' found at: {file_url}")
        else:
            print(f"'{filename}' not found at: {file_url}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {file_url}: {e}")

def get_wordpress_version(content):
    # Busca en el contenido un meta tag o comentario que indique la versión de WordPress
    version = re.search(r'wordpress.org/\?v=([0-9\.]+)', content)
    if version:
        return version.group(1)
    else:
        return None

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
                print(f"Feed found at: {feed_url}")
                version = get_wordpress_version(response.text)
                if version:
                    print(f"WordPress version detected from {feed_path}: {version}")
                else:
                    print(f"WordPress version not found in {feed_path}.")
                found_any_feed = True
            else:
                print(f"Feed not found at: {feed_url}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {feed_url}: {e}")
    
    if not found_any_feed:
        print("No WordPress feeds found.")

def detect_theme(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code == 200:
            # Busca todos los links a archivos CSS en el HTML
            css_files = re.findall(r'<link[^>]+href="([^"]+)"', response.text)
            theme_found = False
            print(css_files)
            for css_file in css_files:
                if '/wp-content/themes/' in css_file:
                    theme_match = re.search(r'/wp-content/themes/([a-zA-Z0-9-_]+)/', css_file)
                    print('/wp-content/themes/')
                    if theme_match:
                        theme_name = theme_match.group(1)
                        print(f"WordPress theme detected: {theme_name}")
                        theme_found = True
                        break
            if not theme_found:
                print("WordPress theme not found in the HTML.")
        else:
            print(f"Error fetching {url}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and display HTTP headers from a given URL and check for specific WordPress files.")
    parser.add_argument("-u", "--url", type=str, required=True, help="The URL to analyze.")
    
    args = parser.parse_args()

    # Fetch and display headers
    get_headers(args.url)
    
    # Check if readme.html exists
    check_file(args.url, "readme.html")
    
    # Check if wp-cron.php exists
    check_file(args.url, "wp-cron.php")

    # Check WordPress feeds
    check_feeds(args.url)
    
    detect_theme(args.url)
