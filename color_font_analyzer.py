#!/usr/bin/env python3
"""
Color and Font Analyzer - Scrapes webpages and extracts comprehensive color and typography information
"""

import re
import json
import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import tinycss2
import webcolors


class ColorNormalizer:
    """Handles color normalization and conversion"""
    
    @staticmethod
    def normalize_color(color_str: str) -> Optional[str]:
        """
        Normalize color to hex format for deduplication
        Converts rgb(), rgba(), hsl(), named colors to hex
        Returns None if invalid color
        """
        if not color_str:
            return None
            
        color_str = color_str.strip().lower()
        
        # Already hex
        if color_str.startswith('#'):
            # Expand shorthand hex (#fff -> #ffffff)
            if len(color_str) == 4:
                return '#' + ''.join([c*2 for c in color_str[1:]])
            return color_str
        
        # Named colors
        try:
            return webcolors.name_to_hex(color_str)
        except (ValueError, AttributeError):
            pass
        
        # RGB/RGBA format
        rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)
        
        # HSL format (convert to RGB first)
        hsl_match = re.match(r'hsla?\s*\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%', color_str)
        if hsl_match:
            h, s, l = map(int, hsl_match.groups())
            # Simplified HSL to RGB conversion
            c = (1 - abs(2 * l / 100 - 1)) * s / 100
            x = c * (1 - abs((h / 60) % 2 - 1))
            m = l / 100 - c / 2
            
            if h < 60:
                r, g, b = c, x, 0
            elif h < 120:
                r, g, b = x, c, 0
            elif h < 180:
                r, g, b = 0, c, x
            elif h < 240:
                r, g, b = 0, x, c
            elif h < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)
        
        return None
    
    @staticmethod
    def get_color_variants(color_str: str) -> List[str]:
        """Get all variant representations of a color"""
        normalized = ColorNormalizer.normalize_color(color_str)
        if not normalized:
            return [color_str]
        
        variants = [normalized, color_str]
        
        # Add named color if possible
        try:
            hex_without_hash = normalized.lstrip('#')
            name = webcolors.hex_to_name('#' + hex_without_hash)
            variants.append(name)
        except (ValueError, AttributeError):
            pass
        
        # Add RGB format
        hex_color = normalized.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            variants.append(f'rgb({r}, {g}, {b})')
        
        return list(set(variants))
    
    @staticmethod
    def calculate_luminance(hex_color: str) -> float:
        """Calculate relative luminance for contrast ratio calculation"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return 0
        
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        
        # Apply gamma correction
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = adjust(r), adjust(g), adjust(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """Calculate WCAG contrast ratio between two colors"""
        l1 = ColorNormalizer.calculate_luminance(color1)
        l2 = ColorNormalizer.calculate_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)


class ColorExtractor:
    """Extracts and categorizes colors from CSS"""
    
    # Categories for color classification
    BACKGROUND_KEYWORDS = ['background', 'bg', 'surface', 'card', 'modal', 'overlay', 'section']
    TEXT_KEYWORDS = ['text', 'color', 'font', 'heading', 'paragraph', 'caption', 'label']
    INTERACTIVE_KEYWORDS = ['button', 'btn', 'link', 'anchor', 'input', 'focus', 'hover', 'active']
    BORDER_KEYWORDS = ['border', 'outline', 'divider', 'separator', 'stroke']
    SEMANTIC_KEYWORDS = {
        'success': ['success', 'positive', 'green', 'valid'],
        'error': ['error', 'danger', 'red', 'invalid', 'alert'],
        'warning': ['warning', 'caution', 'yellow', 'orange'],
        'info': ['info', 'information', 'blue', 'notice']
    }
    
    def __init__(self):
        self.colors = defaultdict(lambda: {
            'value': '',
            'normalized': '',
            'selectors': set(),
            'properties': set(),
            'frequency': 0,
            'css_variables': set(),
            'contrast_contexts': []
        })
    
    def categorize_color(self, selector: str, property_name: str) -> str:
        """Determine color category based on selector and property"""
        selector_lower = selector.lower()
        property_lower = property_name.lower()
        
        # Check semantic colors first
        for category, keywords in self.SEMANTIC_KEYWORDS.items():
            if any(kw in selector_lower for kw in keywords):
                return f'semantic_{category}'
        
        # Check interactive elements
        if any(kw in selector_lower for kw in self.INTERACTIVE_KEYWORDS):
            return 'interactive'
        
        # Check borders
        if 'border' in property_lower or any(kw in selector_lower for kw in self.BORDER_KEYWORDS):
            return 'border'
        
        # Check backgrounds
        if 'background' in property_lower or any(kw in selector_lower for kw in self.BACKGROUND_KEYWORDS):
            return 'background'
        
        # Check text colors
        if property_lower == 'color' or any(kw in selector_lower for kw in self.TEXT_KEYWORDS):
            return 'text'
        
        return 'other'
    
    def extract_from_inline_style(self, element, base_selector: str = ''):
        """Extract colors from inline style attribute"""
        style = element.get('style', '')
        if not style:
            return
        
        # Parse inline styles
        for declaration in style.split(';'):
            if ':' not in declaration:
                continue
            
            prop, value = declaration.split(':', 1)
            prop = prop.strip()
            value = value.strip()
            
            # Check if value contains a color
            color = self._extract_color_from_value(value)
            if color:
                normalized = ColorNormalizer.normalize_color(color)
                if normalized:
                    selector = f'{base_selector}[style*="{prop}"]' if base_selector else f'[style*="{prop}"]'
                    self._add_color(color, normalized, selector, prop)
    
    def extract_from_css_rule(self, rule, css_variables: Dict[str, str]):
        """Extract colors from a CSS rule"""
        if rule.type != 'qualified-rule':
            return
        
        # Get selector
        selector = tinycss2.serialize(rule.prelude).strip()
        
        # Parse declarations from content
        declarations = tinycss2.parse_declaration_list(rule.content)
        
        for declaration in declarations:
            if declaration.type != 'declaration':
                continue
            
            prop_name = declaration.name
            value_tokens = declaration.value
            value_str = tinycss2.serialize(value_tokens)
            
            # Extract CSS variable definitions
            if prop_name.startswith('--'):
                color = self._extract_color_from_value(value_str)
                if color:
                    css_variables[prop_name] = color
            
            # Extract colors from values
            colors = self._extract_colors_from_tokens(value_tokens, css_variables)
            for color in colors:
                normalized = ColorNormalizer.normalize_color(color)
                if normalized:
                    self._add_color(color, normalized, selector, prop_name)
    
    def _extract_color_from_value(self, value: str) -> Optional[str]:
        """Extract first color from a CSS value string"""
        value = value.strip()
        
        # Hex colors
        hex_match = re.search(r'#[0-9a-fA-F]{3,6}', value)
        if hex_match:
            return hex_match.group()
        
        # RGB/RGBA
        rgb_match = re.search(r'rgba?\s*\([^)]+\)', value)
        if rgb_match:
            return rgb_match.group()
        
        # HSL/HSLA
        hsl_match = re.search(r'hsla?\s*\([^)]+\)', value)
        if hsl_match:
            return hsl_match.group()
        
        # Named colors (common ones)
        color_names = [
            'black', 'white', 'red', 'green', 'blue', 'yellow', 'orange', 'purple',
            'pink', 'brown', 'gray', 'grey', 'cyan', 'magenta', 'lime', 'navy',
            'teal', 'olive', 'maroon', 'aqua', 'silver', 'fuchsia'
        ]
        
        for color_name in color_names:
            if re.search(r'\b' + color_name + r'\b', value, re.IGNORECASE):
                return color_name
        
        return None
    
    def _extract_colors_from_tokens(self, tokens, css_variables: Dict[str, str]) -> List[str]:
        """Extract colors from CSS tokens"""
        colors = []
        
        for token in tokens:
            # Hash token (hex colors)
            if token.type == 'hash':
                colors.append('#' + token.value)
            
            # Function token (rgb, rgba, hsl, hsla, var)
            elif token.type == 'function':
                func_name = token.name.lower()
                if func_name in ['rgb', 'rgba', 'hsl', 'hsla']:
                    color_str = f"{func_name}({tinycss2.serialize(token.arguments)})"
                    colors.append(color_str)
                elif func_name == 'var':
                    # Resolve CSS variable
                    var_name = tinycss2.serialize(token.arguments).split(',')[0].strip()
                    if var_name in css_variables:
                        colors.append(css_variables[var_name])
            
            # Ident token (named colors)
            elif token.type == 'ident':
                try:
                    webcolors.name_to_hex(token.value)
                    colors.append(token.value)
                except ValueError:
                    pass
        
        return colors
    
    def _add_color(self, original: str, normalized: str, selector: str, property_name: str):
        """Add a color to the collection"""
        color_data = self.colors[normalized]
        color_data['value'] = original
        color_data['normalized'] = normalized
        color_data['selectors'].add(selector)
        color_data['properties'].add(property_name)
        color_data['frequency'] += 1


class FontExtractor:
    """Extracts typography information from CSS"""
    
    def __init__(self):
        self.fonts = defaultdict(lambda: {
            'family': '',
            'sizes': defaultdict(int),
            'weights': defaultdict(int),
            'line_heights': defaultdict(int),
            'selectors': set(),
            'frequency': 0
        })
    
    def extract_from_css_rule(self, rule):
        """Extract font information from a CSS rule"""
        if rule.type != 'qualified-rule':
            return
        
        # Get selector
        selector = tinycss2.serialize(rule.prelude).strip()
        
        # Parse declarations from content
        declarations = tinycss2.parse_declaration_list(rule.content)
        
        font_family = None
        font_size = None
        font_weight = None
        line_height = None
        
        for declaration in declarations:
            if declaration.type != 'declaration':
                continue
            
            prop_name = declaration.name
            value_str = tinycss2.serialize(declaration.value).strip()
            
            if prop_name == 'font-family':
                font_family = value_str
            elif prop_name == 'font-size':
                font_size = value_str
            elif prop_name == 'font-weight':
                font_weight = value_str
            elif prop_name == 'line-height':
                line_height = value_str
            elif prop_name == 'font':
                # Parse shorthand font property
                parts = value_str.split()
                for i, part in enumerate(parts):
                    if 'px' in part or 'em' in part or 'rem' in part or '%' in part:
                        font_size = part
                        if i + 1 < len(parts):
                            font_family = ' '.join(parts[i + 1:])
                        break
        
        # Store font information
        if font_family:
            # Extract first font from family list, handling quotes properly
            first_font = font_family.split(',')[0].strip()
            # Remove matching quotes from start and end
            if (first_font.startswith('"') and first_font.endswith('"')) or \
               (first_font.startswith("'") and first_font.endswith("'")):
                first_font = first_font[1:-1]
            
            font_key = first_font.strip()
            font_data = self.fonts[font_key]
            font_data['family'] = font_family
            font_data['selectors'].add(selector)
            font_data['frequency'] += 1
            
            if font_size:
                font_data['sizes'][font_size] += 1
            if font_weight:
                font_data['weights'][font_weight] += 1
            if line_height:
                font_data['line_heights'][line_height] += 1


class WebpageAnalyzer:
    """Main analyzer for webpage color and typography"""
    
    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.html_content = None
        self.soup = None
        self.color_extractor = ColorExtractor()
        self.font_extractor = FontExtractor()
        self.css_variables = {}
    
    def fetch_webpage(self) -> bool:
        """Fetch webpage content"""
        try:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                print(f"Error: URL does not return HTML content (content-type: {content_type})")
                return False
            
            self.html_content = response.text
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
            return True
            
        except requests.exceptions.Timeout:
            print(f"Error: Request timeout after {self.timeout} seconds")
            return False
        except requests.exceptions.ConnectionError:
            print("Error: Connection failed - check your internet connection")
            return False
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP error occurred - {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed - {e}")
            return False
    
    def analyze(self) -> 'AnalysisResult':
        """Perform complete analysis"""
        if not self.fetch_webpage():
            return None
        
        print(f"Analyzing: {self.url}")
        
        # Extract from inline styles
        print("  - Extracting inline styles...")
        for element in self.soup.find_all(style=True):
            tag_name = element.name
            classes = ' '.join(element.get('class', []))
            selector = f"{tag_name}.{classes}" if classes else tag_name
            self.color_extractor.extract_from_inline_style(element, selector)
        
        # Extract from <style> tags
        print("  - Parsing <style> tags...")
        for style_tag in self.soup.find_all('style'):
            self._parse_css(style_tag.string or '')
        
        # Extract from external CSS files
        print("  - Fetching external CSS files...")
        for link in self.soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                self._fetch_and_parse_css(href)
        
        print("  - Categorizing colors...")
        colors_by_category = self._categorize_colors()
        
        print("  - Analyzing complete!")
        return AnalysisResult(
            url=self.url,
            colors=dict(self.color_extractor.colors),
            colors_by_category=colors_by_category,
            fonts=dict(self.font_extractor.fonts),
            css_variables=self.css_variables
        )
    
    def _parse_css(self, css_content: str):
        """Parse CSS content and extract colors and fonts"""
        if not css_content:
            return
        
        try:
            rules = tinycss2.parse_stylesheet(css_content)
            
            for rule in rules:
                if rule.type == 'qualified-rule':
                    self.color_extractor.extract_from_css_rule(rule, self.css_variables)
                    self.font_extractor.extract_from_css_rule(rule)
        except Exception as e:
            print(f"  Warning: Error parsing CSS: {e}")
    
    def _fetch_and_parse_css(self, href: str):
        """Fetch and parse external CSS file"""
        try:
            css_url = urljoin(self.url, href)
            
            # Skip external domains
            if urlparse(css_url).netloc != urlparse(self.url).netloc:
                return
            
            response = requests.get(css_url, timeout=self.timeout)
            response.raise_for_status()
            
            self._parse_css(response.text)
            
        except Exception as e:
            print(f"  Warning: Could not fetch CSS from {href}: {e}")
    
    def _categorize_colors(self) -> Dict[str, List[Dict]]:
        """Categorize colors by usage"""
        categories = defaultdict(list)
        
        for normalized_color, data in self.color_extractor.colors.items():
            # Determine category for each selector
            for selector in data['selectors']:
                for prop in data['properties']:
                    category = self.color_extractor.categorize_color(selector, prop)
                    
                    color_info = {
                        'color': data['value'],
                        'normalized': normalized_color,
                        'selector': selector,
                        'property': prop,
                        'frequency': data['frequency']
                    }
                    
                    categories[category].append(color_info)
                    break  # Only categorize once per selector
        
        return dict(categories)


class AnalysisResult:
    """Container for analysis results"""
    
    def __init__(self, url: str, colors: Dict, colors_by_category: Dict, fonts: Dict, css_variables: Dict):
        self.url = url
        self.colors = colors
        self.colors_by_category = colors_by_category
        self.fonts = fonts
        self.css_variables = css_variables
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'total_unique_colors': len(self.colors),
            'total_unique_fonts': len(self.fonts),
            'total_css_variables': len(self.css_variables),
            'colors_by_category': {
                category: len(colors) for category, colors in self.colors_by_category.items()
            }
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        # Convert sets to lists for JSON serialization
        colors_dict = {}
        for color, data in self.colors.items():
            colors_dict[color] = {
                'value': data['value'],
                'normalized': data['normalized'],
                'selectors': list(data['selectors']),
                'properties': list(data['properties']),
                'frequency': data['frequency'],
                'css_variables': list(data['css_variables']),
                'contrast_contexts': data['contrast_contexts']
            }
        
        fonts_dict = {}
        for font, data in self.fonts.items():
            fonts_dict[font] = {
                'family': data['family'],
                'sizes': dict(data['sizes']),
                'weights': dict(data['weights']),
                'line_heights': dict(data['line_heights']),
                'selectors': list(data['selectors']),
                'frequency': data['frequency']
            }
        
        return {
            'url': self.url,
            'summary': self.get_summary(),
            'colors': colors_dict,
            'colors_by_category': self.colors_by_category,
            'fonts': fonts_dict,
            'css_variables': self.css_variables
        }
    
    def print_report(self):
        """Print formatted report to console"""
        print("\n" + "=" * 70)
        print(f"COLOR AND FONT ANALYSIS REPORT")
        print("=" * 70)
        print(f"\nURL: {self.url}")
        
        # Summary
        summary = self.get_summary()
        print("\n--- SUMMARY ---")
        print(f"Total unique colors: {summary['total_unique_colors']}")
        print(f"Total unique fonts: {summary['total_unique_fonts']}")
        print(f"CSS variables defined: {summary['total_css_variables']}")
        
        # Colors by category
        print("\n--- COLORS BY CATEGORY ---")
        for category, colors in self.colors_by_category.items():
            print(f"\n{category.upper().replace('_', ' ')} ({len(colors)} colors):")
            # Show top 5 most frequent colors in each category
            sorted_colors = sorted(colors, key=lambda x: x['frequency'], reverse=True)[:5]
            for color_info in sorted_colors:
                print(f"  • {color_info['normalized']} ({color_info['color']})")
                print(f"    Property: {color_info['property']}")
                print(f"    Selector: {color_info['selector'][:60]}...")
        
        # Fonts
        print("\n--- FONT FAMILIES ---")
        sorted_fonts = sorted(self.fonts.items(), key=lambda x: x[1]['frequency'], reverse=True)
        for font_name, font_data in sorted_fonts[:10]:
            print(f"\n{font_name} (used {font_data['frequency']} times)")
            if font_data['sizes']:
                sizes = ', '.join([f"{size} ({count}x)" for size, count in 
                                  sorted(font_data['sizes'].items(), key=lambda x: x[1], reverse=True)[:3]])
                print(f"  Sizes: {sizes}")
            if font_data['weights']:
                weights = ', '.join([f"{weight} ({count}x)" for weight, count in 
                                    sorted(font_data['weights'].items(), key=lambda x: x[1], reverse=True)[:3]])
                print(f"  Weights: {weights}")
        
        print("\n" + "=" * 70)


def analyze_webpage(url: str, timeout: int = 10) -> Optional[AnalysisResult]:
    """
    Analyze a webpage for colors and typography
    
    Args:
        url: The webpage URL to analyze
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        AnalysisResult object containing analysis data, or None if failed
    """
    analyzer = WebpageAnalyzer(url, timeout)
    return analyzer.analyze()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze webpage colors and typography',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python color_font_analyzer.py https://example.com
  python color_font_analyzer.py https://example.com --output results.json
  python color_font_analyzer.py https://example.com --timeout 30
        """
    )
    
    parser.add_argument('url', help='Website URL to analyze')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--timeout', '-t', type=int, default=10, 
                       help='Request timeout in seconds (default: 10)')
    parser.add_argument('--no-print', action='store_true',
                       help='Skip printing report to console')
    
    args = parser.parse_args()
    
    # Validate URL
    url = args.url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Analyze
    result = analyze_webpage(url, args.timeout)
    
    if not result:
        print("Analysis failed")
        sys.exit(1)
    
    # Print report
    if not args.no_print:
        result.print_report()
    
    # Save to JSON
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nResults saved to: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
