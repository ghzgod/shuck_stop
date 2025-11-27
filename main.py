"""
Main entry point for the Shuck Stop price aggregator.
Scrapes prices from multiple sources and generates a static HTML page.
"""

import logging
import re
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Major brands to include - only trusted shuckable drives
ALLOWED_BRANDS = [
    # Seagate lines
    "seagate",
    "expansion",
    "one touch",
    "backup plus",
    # Western Digital lines
    "western digital",
    "wd",
    "easystore",
    "elements",
    "my book",
    "my passport",
]

# Brands/keywords to exclude (off-brand, enterprise, etc.)
EXCLUDED_KEYWORDS = [
    "avolusion",
    "buslink",
    "oyen",
    "fantom",
    "g-drive",
    "g-technology",
    "lacie",
    "transcend",
    "toshiba canvio",  # Keep Toshiba X300/N300 but exclude Canvio
    "silicon power",
    "adata",
    "sabrent",
    "orico",
    "inateck",
]


def is_major_brand(model: str) -> bool:
    """
    Check if a drive model is from a major brand (Seagate or WD).
    
    Args:
        model: The model name string
        
    Returns:
        True if the drive is from an allowed major brand
    """
    model_lower = model.lower()
    
    # First check exclusions
    for excluded in EXCLUDED_KEYWORDS:
        if excluded in model_lower:
            return False
    
    # Then check if it matches any allowed brand
    for brand in ALLOWED_BRANDS:
        if brand in model_lower:
            return True
    
    return False


def main():
    """Run the scraper and generate the output HTML."""
    from generate_html import DrivePrice, generate_html
    from scrape_diskprices import scrape_diskprices
    from scrape_shucks import scrape_shucks

    all_drives: list[DrivePrice] = []

    # Scrape shucks.top
    logger.info("Scraping shucks.top...")
    try:
        shucks_drives = scrape_shucks()
        logger.info(f"Found {len(shucks_drives)} drives from shucks.top")

        # Convert to common DrivePrice format
        for d in shucks_drives:
            all_drives.append(
                DrivePrice(
                    capacity_tb=d.capacity_tb,
                    model=d.model,
                    source="shucks.top",
                    retailer=d.retailer,
                    price=d.price,
                    url=d.url,
                    price_per_tb=d.price_per_tb,
                    is_available=d.is_available,
                    lowest_ever=getattr(d, "lowest_ever", None),
                    lowest_ever_date=getattr(d, "lowest_ever_date", None),
                )
            )
    except Exception as e:
        logger.error(f"Error scraping shucks.top: {e}")

    # Scrape diskprices.com
    logger.info("Scraping diskprices.com...")
    try:
        diskprices_drives = scrape_diskprices(min_capacity_tb=8)
        logger.info(f"Found {len(diskprices_drives)} drives from diskprices.com")

        # Convert to common DrivePrice format
        for d in diskprices_drives:
            all_drives.append(
                DrivePrice(
                    capacity_tb=d.capacity_tb,
                    model=d.model,
                    source="diskprices.com",
                    retailer=d.retailer,
                    price=d.price,
                    url=d.url,
                    price_per_tb=d.price_per_tb,
                    is_available=d.is_available,
                )
            )
    except Exception as e:
        logger.error(f"Error scraping diskprices.com: {e}")

    # Filter for major brands only
    logger.info(f"Total drives before brand filter: {len(all_drives)}")
    all_drives = [d for d in all_drives if is_major_brand(d.model)]
    logger.info(f"Total drives after brand filter (Seagate/WD only): {len(all_drives)}")

    # Deduplicate - prefer lower prices when same capacity/retailer
    logger.info(f"Total drives before deduplication: {len(all_drives)}")
    all_drives = deduplicate_drives(all_drives)
    logger.info(f"Total drives after deduplication: {len(all_drives)}")

    if not all_drives:
        logger.error("No drives found! Check if websites are accessible.")
        sys.exit(1)

    # Generate HTML output
    output_dir = Path(__file__).parent / "docs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "index.html"

    logger.info(f"Generating HTML output to {output_path}")
    generate_html(all_drives, str(output_path))

    logger.info("Done! Generated index.html")

    # Print summary
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY (Major Brands Only: Seagate & WD)")
    print("=" * 60)

    # Count by source
    sources = {}
    for d in all_drives:
        sources[d.source] = sources.get(d.source, 0) + 1

    for source, count in sources.items():
        print(f"  {source}: {count} drives")

    # Best deals
    print("\n" + "-" * 60)
    print("BEST DEALS BY CAPACITY:")
    print("-" * 60)

    best = {}
    for d in all_drives:
        if d.is_available and d.price_per_tb:
            cap = int(d.capacity_tb)
            if cap not in best or d.price_per_tb < best[cap].price_per_tb:
                best[cap] = d

    for cap in sorted(best.keys()):
        d = best[cap]
        print(f"  {cap}TB: ${d.price:.2f} (${d.price_per_tb:.2f}/TB) - {d.retailer} - {d.model[:40]}")


def deduplicate_drives(drives: list) -> list:
    """
    Remove duplicate drives, keeping the lowest price for each capacity/model/retailer combo.
    """
    seen = {}
    for d in drives:
        key = (int(d.capacity_tb), d.model.lower(), d.retailer.lower())
        if key not in seen:
            seen[key] = d
        elif d.price and d.is_available:
            # Keep if lower price or current is unavailable
            existing = seen[key]
            if not existing.price or not existing.is_available or d.price < existing.price:
                seen[key] = d

    return list(seen.values())


if __name__ == "__main__":
    main()
