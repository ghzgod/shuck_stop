# Shuck Stop 🖴

A hard drive price aggregator that scrapes prices from multiple sources and generates a static HTML comparison page. Perfect for finding the best deals on external HDDs for shucking.

## Features

- **Multi-source scraping**: Aggregates prices from [shucks.top](https://shucks.top) and [diskprices.com](https://diskprices.com)
- **Price per TB calculations**: Automatically calculates and displays $/TB for easy comparison
- **Best deal highlights**: Shows the best available price for each capacity tier
- **Color-coded pricing**: Visual indicators for deal quality based on $/TB
- **Automatic updates**: GitHub Actions workflow updates prices every 12 hours
- **Static hosting**: Deploy for free on GitHub Pages

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

Install uv:

```bash
# Linux/macOS
curl -sSL https://install.uv.sh | bash

# macOS with Homebrew
brew install uv
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/shuck-stop.git
cd shuck-stop

# Install dependencies
uv sync
```

### Usage

Run the scraper and generate the HTML:

```bash
uv run python main.py
```

The output will be generated at `docs/index.html`.

### Local Development

To test locally, you can serve the generated HTML:

```bash
# Python's built-in server
uv run python -m http.server --directory docs 8000
```

Then open http://localhost:8000 in your browser.

## Deployment

### GitHub Pages

1. Push your code to GitHub
2. Go to repository Settings → Pages
3. Set Source to "Deploy from a branch"
4. Select the `master` branch and `/docs` folder
5. Save

The GitHub Actions workflow will automatically update prices every 12 hours.

### Manual Trigger

You can manually trigger an update:

1. Go to Actions tab in your repository
2. Select "Update Prices" workflow
3. Click "Run workflow"

## Project Structure

```
shuck_stop/
├── main.py                 # Main entry point
├── scrape_shucks.py        # Scraper for shucks.top
├── scrape_diskprices.py    # Scraper for diskprices.com
├── generate_html.py        # HTML generator
├── docs/
│   └── index.html          # Generated output (for GitHub Pages)
├── .github/
│   └── workflows/
│       └── update-prices.yml   # Scheduled update workflow
├── scripts/
│   └── check-uv.sh         # Preflight check script
├── pyproject.toml          # Project configuration
├── uv.lock                 # Lock file
└── README.md
```

## Price Grading Scale

Based on the shucks.top scale where $17/TB is average and $15/TB is ideal:

| $/TB Range | Grade | Meaning |
|------------|-------|---------|
| ≤$12 | 🔥 Excellent | Incredible deal - buy immediately |
| ≤$13 | 💸 Great | Great price |
| ≤$15 | ✅ Good | Good deal |
| ≤$17 | ➖ Fair | Fair/average price |
| ≤$20 | ⚠️ Meh | Below average |
| >$20 | ❌ Bad | Overpriced |

## Data Sources

- **[shucks.top](https://shucks.top)**: WD external drive price tracker with historical data
- **[diskprices.com](https://diskprices.com)**: Aggregated disk prices from Amazon

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [shucks.top](https://shucks.top) for the original price tracking
- [diskprices.com](https://diskprices.com) for Amazon price data
- The r/DataHoarder community for inspiring this project

