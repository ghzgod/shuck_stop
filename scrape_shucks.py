"""
Scraper for shucks.top - WD external drive price tracker.
"""

import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class DrivePrice:
    """Represents a hard drive price entry."""

    capacity_tb: int
    model: str
    source: str
    retailer: str
    price: Optional[float]
    url: Optional[str]
    price_per_tb: Optional[float] = None
    is_available: bool = True
    lowest_ever: Optional[float] = None
    lowest_ever_date: Optional[str] = None

    def __post_init__(self):
        if self.price and self.capacity_tb:
            self.price_per_tb = round(self.price / self.capacity_tb, 2)


def parse_price(price_str: str) -> Optional[float]:
    """Extract numeric price from string like '$234.99'."""
    if not price_str or price_str == "—":
        return None
    match = re.search(r"\$?([\d,]+\.?\d*)", price_str.replace(",", ""))
    if match:
        return float(match.group(1))
    return None


def scrape_shucks() -> list[DrivePrice]:
    """
    Scrape hard drive prices from shucks.top.

    Returns:
        List of DrivePrice objects with current prices from various retailers.
    """
    url = "https://shucks.top/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")
    drives = []

    # Find the main data table
    table = soup.find("table")
    if not table:
        return drives

    # Get header info to map columns to retailers
    thead = table.find("thead")
    if not thead:
        return drives

    header_row = thead.find("tr")
    headers = []
    for th in header_row.find_all("th"):
        # Check for retailer SVG icons or text
        svg = th.find("svg")
        if svg:
            # Try to identify retailer from SVG path or title
            path_data = str(svg)
            if "amazon" in path_data.lower() or "f90" in path_data:  # Amazon orange
                headers.append("amazon")
            elif "bestbuy" in path_data.lower() or "ffed31" in path_data:  # Best Buy yellow
                headers.append("bestbuy")
            elif "bf291a" in path_data.lower() or "PHOTO" in path_data:  # B&H red
                headers.append("bh")
            elif "ebay" in path_data.lower() or "e53238" in path_data:  # eBay colors
                headers.append("ebay")
            elif "newegg" in path_data.lower() or "f7ed1a" in path_data:  # Newegg egg
                headers.append("newegg")
            else:
                headers.append("unknown")
        else:
            text = th.get_text(strip=True).lower()
            headers.append(text if text else "unknown")

    # Parse table body
    tbody = table.find("tbody")
    if not tbody:
        return drives

    retailer_map = {
        "amazon": "Amazon",
        "bestbuy": "Best Buy",
        "bh": "B&H Photo",
        "ebay": "eBay",
        "newegg": "Newegg",
    }

    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        # Extract capacity
        capacity_text = cells[0].get_text(strip=True)
        capacity_match = re.search(r"(\d+)\s*TB", capacity_text)
        if not capacity_match:
            continue
        capacity_tb = int(capacity_match.group(1))

        # Extract model
        model = cells[1].get_text(strip=True)

        # Extract lowest ever price if available
        lowest_ever = None
        lowest_ever_date = None
        if len(cells) >= 8:
            lowest_cell = cells[7]
            lowest_price_elem = lowest_cell.find("p")
            if lowest_price_elem:
                lowest_ever = parse_price(lowest_price_elem.get_text(strip=True))
            date_elem = lowest_cell.find("p", class_="ago")
            if date_elem:
                lowest_ever_date = date_elem.get_text(strip=True)

        # Process retailer columns (columns 2-6 typically)
        for idx, cell in enumerate(cells[2:7], start=2):
            if idx >= len(headers):
                continue

            retailer_key = headers[idx]
            if retailer_key not in retailer_map:
                continue

            retailer = retailer_map[retailer_key]

            # Check if this cell has a price link
            link = cell.find("a")
            if not link:
                continue

            link_text = link.get_text(strip=True)
            href = link.get("href", "")

            # Skip "check" links (no price) and unavailable items
            if link_text.lower() == "check":
                continue

            price = parse_price(link_text)
            if not price:
                continue

            # Check availability - look for 'oos' class
            is_available = "oos" not in cell.get("class", [])

            drive = DrivePrice(
                capacity_tb=capacity_tb,
                model=model,
                source="shucks.top",
                retailer=retailer,
                price=price,
                url=href,
                is_available=is_available,
                lowest_ever=lowest_ever,
                lowest_ever_date=lowest_ever_date,
            )
            drives.append(drive)

    return drives


if __name__ == "__main__":
    drives = scrape_shucks()
    for drive in drives:
        print(
            f"{drive.capacity_tb}TB {drive.model} @ {drive.retailer}: "
            f"${drive.price} (${drive.price_per_tb}/TB) - {'Available' if drive.is_available else 'OOS'}"
        )

