import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import argparse
from collections import defaultdict



# small tool-set for grabbing dir from View-Source

# Ppattern
dir_pattern = re.compile(r"/[a-zA-Z0-9_-]+/")
style_pattern = re.compile(r'url\(["\']?(/[^"\']+)["\']?\)')

def find_directories(url):
    #  URL  scheme (http/https)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url  

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Failed to fetch {url} (Status Code: {response.status_code})")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        directories = set()  

       # attr to check
        attrs_to_check = ["href", "src", "action", "data", "data-src", "data-href"]

        # Extract directories from relevant tags
        for tag in soup.find_all():
            for attr in attrs_to_check:
                attr_value = tag.get(attr)
                if attr_value:
                    full_url = urljoin(url, attr_value)  # Convert to absolute URL
                    parsed = urlparse(full_url)
                    path = parsed.path.strip("/")

                    # Capture directory structure
                    if "/" in path and not path.endswith(('.css', '.js', '.jpg', '.png', '.gif', '.svg', '.ico', '.json', '.xml')):
                        dir_path = "/" + path.split("/")[0] + "/"
                        directories.add(dir_path)

        # Extract directories from comments
        for comment in soup.findAll(string=lambda text: isinstance(text, str) and "/" in text):
            directories.update(dir_pattern.findall(comment))

        # Extract possible paths from inline JS
        for script in soup.find_all("script"):
            if script.string:
                directories.update(re.findall(r'["\'](/[^"\']+/)["\']', script.string))

        # Extract URLs from meta tags
        for meta_tag in soup.find_all("meta"):
            content = meta_tag.get("content")
            if content and "/" in content:
                directories.update(dir_pattern.findall(content))

        # Extract from inline styles
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                directories.update(style_pattern.findall(style_tag.string))

        # Display results
        if directories:
            print("\n[+] Possible Directories :")
            for d in sorted(directories):
                print(f"- {d}")
        else:
            print("\n[*] No directories found.")
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

# Argument parsing for  input
parser = argparse.ArgumentParser(description="Scan a website for possible directories.")
parser.add_argument('url', help="The website URL to scan")
args = parser.parse_args()

find_directories(args.url)
