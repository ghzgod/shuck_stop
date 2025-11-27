"""
Scraper for diskprices.com - Aggregated disk prices from Amazon.
"""

import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class DrivePrice:
    """Represents a hard drive price entry."""

    capacity_tb: float
    model: str
    source: str
    retailer: str
    price: Optional[float]
    url: Optional[str]
    price_per_tb: Optional[float] = None
    is_available: bool = True
    condition: str = "New"
    disk_type: str = "External HDD"

    def __post_init__(self):
        if self.price and self.capacity_tb:
            self.price_per_tb = round(self.price / self.capacity_tb, 2)


def parse_capacity(capacity_str: str) -> Optional[float]:
    """Parse capacity string like '8 TB' or '12TB' or '26 TB x2' to float TB value."""
    if not capacity_str:
        return None
    # Handle TB with optional multiplier (e.g., "12 TB x20" means 20 units of 12TB)
    # For our purposes, we want the single unit capacity
    match = re.search(r"([\d.]+)\s*TB", capacity_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    # Handle GB (convert to TB)
    match = re.search(r"([\d.]+)\s*GB", capacity_str, re.IGNORECASE)
    if match:
        return float(match.group(1)) / 1000
    return None


def parse_price(price_str: str) -> Optional[float]:
    """Extract numeric price from string like '$234.99' or '$1,234' or '234.99'."""
    if not price_str:
        return None
    # Remove commas and find the number after $
    cleaned = price_str.replace(",", "")
    match = re.search(r"\$?([\d]+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None


def scrape_diskprices(min_capacity_tb: int = 8) -> list[DrivePrice]:
    """
    Scrape hard drive prices from diskprices.com.

    Args:
        min_capacity_tb: Minimum capacity to filter (default 8TB)

    Returns:
        List of DrivePrice objects with current Amazon prices.
    """
    url = f"https://diskprices.com/?locale=us&condition=new&capacity={min_capacity_tb}-&disk_types=external_hdd"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")
    drives = []

    # Find the main data table
    # diskprices.com table structure (by column index):
    # 0: Hidden sort value
    # 1: Price per TB (e.g., $10.38)
    # 2: Actual price (e.g., $270)
    # 3: Capacity (e.g., 26 TB)
    # 4: Warranty (may be empty)
    # 5: Type (e.g., External 3.5")
    # 6: Subtype (e.g., HDD)
    # 7: Condition (e.g., New)
    # 8: Product name with Amazon link

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 9:
                continue

            try:
                # Extract data by column position
                price_per_tb_str = cells[1].get_text(strip=True)
                price_str = cells[2].get_text(strip=True)
                capacity_str = cells[3].get_text(strip=True)
                disk_type_str = cells[5].get_text(strip=True)
                subtype_str = cells[6].get_text(strip=True)
                condition_str = cells[7].get_text(strip=True)

                # Get product name and link from last cell
                product_cell = cells[8]
                link = product_cell.find("a")
                if not link:
                    continue

                model = link.get_text(strip=True)
                href = link.get("href", "")

                # Only process Amazon links
                if "amazon" not in href.lower():
                    continue

                # Parse values
                capacity = parse_capacity(capacity_str)
                if not capacity or capacity < min_capacity_tb:
                    continue

                price = parse_price(price_str)
                if not price or price < 10:  # Skip unreasonably low prices
                    continue

                # Skip non-HDD items (SSDs, tape drives, etc.)
                if "SSD" in subtype_str.upper() or "TAPE" in disk_type_str.upper():
                    continue

                # Only include external HDDs
                if "External" not in disk_type_str:
                    continue

                # Clean up model name - remove capacity from it
                model_clean = re.sub(r"\d+\s*TB", "", model).strip()
                if not model_clean or len(model_clean) < 3:
                    model_clean = "External HDD"

                drive = DrivePrice(
                    capacity_tb=capacity,
                    model=model_clean[:100],  # Truncate long names
                    source="diskprices.com",
                    retailer="Amazon",
                    price=price,
                    url=href,
                    is_available=True,
                    condition=condition_str,
                    disk_type=f"{disk_type_str} {subtype_str}".strip(),
                )
                drives.append(drive)

            except (IndexError, ValueError, AttributeError):
                # Skip malformed rows
                continue

    # Remove duplicates based on URL
    seen_urls = set()
    unique_drives = []
    for drive in drives:
        if drive.url and drive.url not in seen_urls:
            seen_urls.add(drive.url)
            unique_drives.append(drive)

    return unique_drives


if __name__ == "__main__":
    drives = scrape_diskprices()
    print(f"Found {len(drives)} external HDD drives from diskprices.com")
    for drive in sorted(drives, key=lambda d: d.price_per_tb or float("inf"))[:20]:
        print(
            f"{drive.capacity_tb}TB {drive.model[:50]} @ Amazon: "
            f"${drive.price:.2f} (${drive.price_per_tb:.2f}/TB)"
        )
