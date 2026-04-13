"""
parser.py — HTML/data extraction functions for the Arma Reforger Workshop scraper.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup


def parse_mod_card(card_element) -> dict:
    """Extract basic mod data from a workshop listing card element."""
    data = {}

    # Mod ID — usually in the href of the card link
    link = card_element.find("a", href=True)
    if link:
        match = re.search(r'/workshop/([A-F0-9]+)', link["href"], re.IGNORECASE)
        if match:
            data["id"] = match.group(1).upper()
            data["workshop_url"] = f"https://reforger.armaplatform.com/workshop/{data['id']}"

    # Name
    name_el = card_element.find(class_=re.compile(r'name|title', re.I))
    if name_el:
        data["name"] = name_el.get_text(strip=True)

    # Author
    author_el = card_element.find(class_=re.compile(r'author|creator', re.I))
    if author_el:
        data["author"] = author_el.get_text(strip=True)

    # Thumbnail
    img = card_element.find("img")
    if img:
        data["thumbnail_url"] = img.get("src") or img.get("data-src")

    # Rating (0–100 percentage)
    rating_el = card_element.find(class_=re.compile(r'rating|score', re.I))
    if rating_el:
        text = rating_el.get_text(strip=True).replace("%", "")
        try:
            data["rating"] = float(text)
        except ValueError:
            data["rating"] = None

    # Size
    size_el = card_element.find(class_=re.compile(r'size|filesize', re.I))
    if size_el:
        data["size_bytes"] = parse_size_to_bytes(size_el.get_text(strip=True))

    # Tags
    tags = []
    for tag_el in card_element.find_all(class_=re.compile(r'tag', re.I)):
        tag_text = tag_el.get_text(strip=True)
        if tag_text:
            tags.append(tag_text)
    if tags:
        data["tags"] = tags

    return data


def parse_mod_detail(html: str) -> dict:
    """Extract full mod data from a mod detail page HTML string."""
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # Description
    desc_el = soup.find(class_=re.compile(r'description|summary|about', re.I))
    if desc_el:
        data["description"] = desc_el.get_text(separator="\n", strip=True)

    # Screenshot image URLs
    images = []
    gallery = soup.find(class_=re.compile(r'gallery|screenshots|media', re.I))
    if gallery:
        for img in gallery.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                images.append(src)
    data["image_urls"] = images

    # Download count
    dl_el = soup.find(class_=re.compile(r'download', re.I))
    if dl_el:
        dl_text = re.sub(r'[^\d]', '', dl_el.get_text())
        if dl_text:
            data["download_count"] = int(dl_text)

    # Created / updated dates
    for meta in soup.find_all("time"):
        dt_str = meta.get("datetime") or meta.get_text(strip=True)
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            label = meta.find_parent().get_text(strip=True).lower() if meta.find_parent() else ""
            if "creat" in label or "publish" in label:
                data["created_at"] = dt
            elif "updat" in label or "edit" in label:
                data["updated_at"] = dt
        except (ValueError, AttributeError):
            pass

    return data


def parse_size_to_bytes(size_str: str) -> Optional[int]:
    """Convert human-readable size string to bytes. E.g. '23.5 MB' → 24660992."""
    size_str = size_str.strip()
    match = re.match(r'([\d.,]+)\s*(B|KB|MB|GB|TB)?', size_str, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "B").upper()
    multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return int(value * multipliers.get(unit, 1))


def extract_mod_id_from_url(url: str) -> Optional[str]:
    """Extract mod ID from a workshop URL."""
    match = re.search(r'/workshop/([A-F0-9]+)', url, re.IGNORECASE)
    return match.group(1).upper() if match else None
