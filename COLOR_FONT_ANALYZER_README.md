# Color and Font Analyzer

A Python tool for extracting and analyzing comprehensive color and typography information from webpages. The analyzer categorizes colors by their semantic usage (backgrounds, text, interactive elements, borders, and semantic/status colors) and provides detailed font usage analysis.

## Features

- **Comprehensive Color Extraction**: Extracts colors from inline styles, `<style>` tags, and external CSS files
- **Color Categorization**: Automatically categorizes colors by usage:
  - Background surfaces (main backgrounds, cards, modals)
  - Text colors (primary, secondary, muted)
  - Interactive elements (buttons, links, inputs, focus states)
  - Borders and dividers
  - Semantic colors (success, error, warning, info)
- **Color Normalization**: Normalizes colors to hex format for deduplication (e.g., `#fff`, `white`, and `rgb(255,255,255)` are treated as the same)
- **CSS Variables Support**: Extracts and resolves CSS custom properties
- **Contrast Ratio Calculation**: WCAG-compliant contrast ratio analysis
- **Font Analysis**: Extracts font families, sizes, weights, and line heights
- **Multiple Output Formats**: Console report and JSON export

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

The required packages are:
- `requests` - for HTTP requests
- `beautifulsoup4` - for HTML parsing
- `tinycss2` - for CSS parsing
- `webcolors` - for color name conversion

## Usage

### Command Line Interface

Basic usage:
```bash
python color_font_analyzer.py https://example.com
```

Save results to JSON:
```bash
python color_font_analyzer.py https://example.com --output results.json
```

Adjust timeout:
```bash
python color_font_analyzer.py https://example.com --timeout 30
```

Skip console output (only save JSON):
```bash
python color_font_analyzer.py https://example.com --output results.json --no-print
```

### As a Python Module

```python
from color_font_analyzer import analyze_webpage

# Analyze a webpage
result = analyze_webpage('https://example.com')

# Access the results
print(result.get_summary())
print(result.colors_by_category)
print(result.fonts)

# Print formatted report
result.print_report()

# Export to dictionary for JSON serialization
data = result.to_dict()
```

## Output Format

### Console Report

The tool generates a formatted report showing:
- Summary statistics (total unique colors, fonts, CSS variables)
- Colors organized by category with usage details
- Font families with size and weight information
- Contrast ratios for text colors

Example output:
```
======================================================================
COLOR AND FONT ANALYSIS REPORT
======================================================================

URL: https://example.com

--- SUMMARY ---
Total unique colors: 33
Total unique fonts: 2
CSS variables defined: 6

--- COLORS BY CATEGORY ---

TEXT (7 colors):
  • #333333 (#333333)
    Property: color
    Selector: body...

--- FONT FAMILIES ---

Helvetica Neue (used 5 times)
  Sizes: 16px (3x), 14px (2x)
  Weights: normal (3x), bold (2x)
```

### JSON Output

The JSON export includes complete analysis data:

```json
{
  "url": "https://example.com",
  "summary": {
    "total_unique_colors": 33,
    "total_unique_fonts": 2,
    "total_css_variables": 6,
    "colors_by_category": {
      "background": 5,
      "text": 7,
      "interactive": 8,
      "border": 3,
      "semantic_success": 4,
      "semantic_error": 6
    }
  },
  "colors": {
    "#007bff": {
      "value": "#007bff",
      "normalized": "#007bff",
      "selectors": [".button", ".link"],
      "properties": ["background-color", "color"],
      "frequency": 5,
      "css_variables": ["--primary-color"],
      "contrast_contexts": []
    }
  },
  "colors_by_category": {
    "text": [
      {
        "color": "#333333",
        "normalized": "#333333",
        "selector": "body",
        "property": "color",
        "frequency": 1
      }
    ]
  },
  "fonts": {
    "Arial": {
      "family": "Arial, sans-serif",
      "sizes": {"16px": 3, "14px": 2},
      "weights": {"normal": 3, "bold": 2},
      "line_heights": {"1.5": 2},
      "selectors": ["body", "p", ".text"],
      "frequency": 5
    }
  },
  "css_variables": {
    "--primary-color": "#007bff",
    "--secondary-color": "#6c757d"
  }
}
```

## Color Categorization Logic

The analyzer uses intelligent pattern matching to categorize colors:

1. **Semantic Colors** (highest priority): Detected by keywords in selectors:
   - Success: `success`, `positive`, `green`, `valid`
   - Error: `error`, `danger`, `red`, `invalid`, `alert`
   - Warning: `warning`, `caution`, `yellow`, `orange`
   - Info: `info`, `information`, `blue`, `notice`

2. **Interactive Elements**: Keywords like `button`, `link`, `input`, `focus`, `hover`, `active`

3. **Borders**: `border`, `outline`, `divider`, `separator` in property names or selectors

4. **Backgrounds**: `background`, `bg`, `surface`, `card`, `modal` keywords or `background-*` properties

5. **Text**: `color` property or `text`, `font`, `heading`, `paragraph` keywords

## Features in Detail

### Color Normalization

All color formats are normalized to hex for accurate deduplication:
- Hex: `#fff` → `#ffffff`
- RGB: `rgb(255, 0, 0)` → `#ff0000`
- RGBA: `rgba(255, 0, 0, 0.5)` → `#ff0000` (alpha ignored for matching)
- HSL: `hsl(0, 100%, 50%)` → `#ff0000`
- Named: `red` → `#ff0000`

### Contrast Ratio Calculation

The tool calculates WCAG 2.1 contrast ratios between colors:
- Uses relative luminance formula
- Helpful for accessibility audits
- Example: Black text on white background = 21:1 ratio

### CSS Variable Resolution

- Extracts CSS custom properties (e.g., `--primary-color: #007bff`)
- Resolves `var()` references in color values
- Tracks which variables are used for each color

## Error Handling

The analyzer gracefully handles:
- Network errors (timeouts, connection failures)
- HTTP errors (404, 500, etc.)
- Malformed HTML/CSS
- External CSS files from different domains (skipped)
- Invalid color values (ignored)

## Limitations

- Does not execute JavaScript (colors from JS-generated styles won't be captured)
- External CSS from different domains is skipped for security
- Alpha channel in colors is ignored for normalization
- Computed styles are not analyzed (only declared styles)
- Limited to colors and fonts explicitly defined in CSS

## Examples

### Analyze a website and save results:
```bash
python color_font_analyzer.py https://getbootstrap.com --output bootstrap_colors.json
```

### Use in a Python script:
```python
from color_font_analyzer import analyze_webpage
import json

# Analyze multiple pages
urls = ['https://site1.com', 'https://site2.com']
results = {}

for url in urls:
    result = analyze_webpage(url, timeout=15)
    if result:
        results[url] = result.to_dict()

# Save combined results
with open('multi_site_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### Extract only specific color categories:
```python
from color_font_analyzer import analyze_webpage

result = analyze_webpage('https://example.com')

# Get only semantic colors
semantic_colors = {
    k: v for k, v in result.colors_by_category.items()
    if k.startswith('semantic_')
}

print(f"Found {len(semantic_colors)} semantic color categories")
```

## Testing

Run the test suite:
```bash
python test_color_font_analyzer.py
```

Tests cover:
- Color normalization (hex, rgb, hsl, named colors)
- Color variant generation
- Contrast ratio calculation
- Color categorization logic
- Font extraction
- Result serialization

## Contributing

Contributions are welcome! Areas for improvement:
- Support for more CSS color formats (color-mix, currentColor, etc.)
- Better font shorthand property parsing
- Gradient color extraction
- Screenshot-based color extraction
- Accessibility score calculation
- Theme detection (light/dark mode colors)

## License

MIT License - see LICENSE file for details
