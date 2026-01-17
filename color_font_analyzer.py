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
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


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
    
    def __init__(self, url: str, timeout: int = 10, skip_fetch: bool = False, 
                 html_content = None, soup = None, use_playwright: bool = True):
        self.url = url
        self.timeout = timeout
        self.html_content = html_content
        self.soup = soup
        self.skip_fetch = skip_fetch
        self.use_playwright = use_playwright
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
        print(f"Analyzing: {self.url}")
        if self.use_playwright:
            print("  - Sampling computed styles with Playwright...")
            samples = self._sample_elements_with_playwright()
            if not samples:
                return None
            print("  - Filtering and ranking colors...")
            processed_samples, ranked_colors, tokens = self._process_samples(samples)
            print("  - Analyzing complete!")
            return AnalysisResult(
                url=self.url,
                colors={},
                colors_by_category={},
                fonts={},
                css_variables={},
                computed_samples=processed_samples,
                ranked_colors=ranked_colors,
                tokens=tokens
            )
        
        if not self.skip_fetch:
            if not self.fetch_webpage():
                return None
        
        if any(item is None for item in [self.html_content, self.soup]):
            return None

        print("  - Extracting inline styles...")
        for element in self.soup.find_all(style=True):
            tag_name = element.name
            classes = ' '.join(element.get('class', []))
            selector = f"{tag_name}.{classes}" if classes else tag_name
            self.color_extractor.extract_from_inline_style(element, selector)
        
        print("  - Parsing <style> tags...")
        for style_tag in self.soup.find_all('style'):
            self._parse_css(style_tag.string or '')
        
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

    def _sample_elements_with_playwright(self) -> List[Dict]:
        """Use Playwright to sample computed styles from real elements"""
        script = r"""
() => {
  const samples = [];
  const toNumber = (v) => {
    const n = parseFloat(v || '0');
    return Number.isFinite(n) ? n : 0;
  };
  const getSelector = (el) => {
    const cls = el.className && typeof el.className === 'string' ? el.className.trim().split(/\s+/).slice(0, 2) : [];
    const clsPart = cls.length ? '.' + cls.join('.') : '';
    return el.tagName.toLowerCase() + clsPart;
  };
  const pushEl = (el, type) => {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    const style = window.getComputedStyle(el);
    samples.push({
      type,
      tag: el.tagName.toLowerCase(),
      selector: getSelector(el),
      width: rect.width,
      height: rect.height,
      area: rect.width * rect.height,
      color: style.color,
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      borderTopWidth: style.borderTopWidth,
      borderRightWidth: style.borderRightWidth,
      borderBottomWidth: style.borderBottomWidth,
      borderLeftWidth: style.borderLeftWidth
    });
  };

  pushEl(document.body, 'body');
  pushEl(document.querySelector('main'), 'main');

  const topByArea = (elements, limit) => {
    return elements
      .map(el => ({ el, area: el.getBoundingClientRect().width * el.getBoundingClientRect().height }))
      .filter(item => item.area > 0)
      .sort((a, b) => b.area - a.area)
      .slice(0, limit)
      .map(item => item.el);
  };

  const containers = topByArea(Array.from(document.querySelectorAll('main, section, article, div, .card, .panel, .container, [class*="card"], [class*="panel"], [class*="section"]')), 6);
  containers.forEach(el => pushEl(el, 'container'));

  const buttons = topByArea(Array.from(document.querySelectorAll('button, [role="button"], .btn, .button, input[type="button"], input[type="submit"]')), 6);
  buttons.forEach(el => pushEl(el, 'button'));

  const links = topByArea(Array.from(document.querySelectorAll('a[href]')), 8);
  links.forEach(el => pushEl(el, 'link'));

  const headings = topByArea(Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')), 10);
  headings.forEach(el => pushEl(el, 'heading'));

  const paragraphs = topByArea(Array.from(document.querySelectorAll('p')), 10);
  paragraphs.forEach(el => pushEl(el, 'paragraph'));

  return samples;
}
"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.url, timeout=self.timeout * 1000, wait_until='domcontentloaded')
                samples = page.evaluate(script)
                browser.close()
                return samples or []
        except PlaywrightTimeoutError:
            print(f"Error: Playwright timeout after {self.timeout} seconds")
            return []
        except Exception as e:
            print(f"Error: Playwright failed - {e}")
            return []

    def _process_samples(self, samples: List[Dict]) -> Tuple[List[Dict], Dict, Dict]:
        """Filter sampled elements, rank colors by visual impact, and infer tokens"""
        processed_samples = []
        items = []

        for sample in samples:
            width = float(sample.get('width', 0))
            height = float(sample.get('height', 0))
            area = float(sample.get('area', 0))
            if area <= 0:
                continue

            border_widths = [
                self._safe_float(sample.get('borderTopWidth')),
                self._safe_float(sample.get('borderRightWidth')),
                self._safe_float(sample.get('borderBottomWidth')),
                self._safe_float(sample.get('borderLeftWidth'))
            ]
            has_visible_border = any(w >= 1 for w in border_widths)

            is_tiny = width <= 1 or height <= 1 or area <= 1

            color = self._normalize_computed_color(sample.get('color'))
            background = self._normalize_computed_color(sample.get('backgroundColor'))
            border = self._normalize_computed_color(sample.get('borderColor'))

            if is_tiny and not has_visible_border:
                color = None
                background = None

            if border and not has_visible_border:
                border = None

            filtered = {
                'type': sample.get('type'),
                'tag': sample.get('tag'),
                'selector': sample.get('selector'),
                'width': width,
                'height': height,
                'area': area,
                'color': color,
                'backgroundColor': background,
                'borderColor': border
            }

            if not any([color, background, border]):
                continue

            processed_samples.append(filtered)

            if color:
                items.append({
                    'role': 'text',
                    'color': color,
                    'area': area,
                    'type': sample.get('type')
                })
            if background:
                items.append({
                    'role': 'background',
                    'color': background,
                    'area': area,
                    'type': sample.get('type')
                })
            if border:
                items.append({
                    'role': 'border',
                    'color': border,
                    'area': area,
                    'type': sample.get('type')
                })

        ranked_colors = self._rank_colors(items)
        tokens = self._infer_tokens(items, ranked_colors)

        return processed_samples, ranked_colors, tokens

    def _rank_colors(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """Rank colors by visual impact: score = area_sum * occurrence_count"""
        counts = defaultdict(int)
        area_sums = defaultdict(float)
        type_sets = defaultdict(set)

        for item in items:
            key = (item['role'], item['color'])
            counts[key] += 1
            area_sums[key] += item['area']
            type_sets[key].add(item.get('type'))

        ranked = defaultdict(list)
        for (role, color), count in counts.items():
            score = area_sums[(role, color)] * count
            ranked[role].append({
                'color': color,
                'score': score,
                'occurrence_count': count,
                'area_sum': area_sums[(role, color)],
                'sample_types': sorted(type_sets[(role, color)])
            })

        for role in ranked:
            ranked[role].sort(key=lambda x: x['score'], reverse=True)

        return dict(ranked)

    def _infer_tokens(self, items: List[Dict], ranked_colors: Dict[str, List[Dict]]) -> Dict[str, Optional[str]]:
        """Infer widget tokens from ranked colors"""
        def top_color_for(role: str, allowed_types: Set[str]) -> Optional[str]:
            filtered = [item for item in items if item['role'] == role and item.get('type') in allowed_types]
            if not filtered:
                return None
            ranked = self._rank_colors(filtered).get(role, [])
            return ranked[0]['color'] if ranked else None

        def top_colors_for(role: str, allowed_types: Set[str], limit: int = 3) -> List[str]:
            filtered = [item for item in items if item['role'] == role and item.get('type') in allowed_types]
            ranked = self._rank_colors(filtered).get(role, [])
            return [entry['color'] for entry in ranked[:limit]]

        widget_bg = top_color_for('background', {'body', 'main', 'container'})
        border = top_color_for('border', {'container', 'body', 'main'})
        text_primary = top_color_for('text', {'heading', 'paragraph'})

        text_candidates = top_colors_for('text', {'heading', 'paragraph'}, limit=3)
        text_muted = text_candidates[1] if len(text_candidates) > 1 else None

        accent = top_color_for('background', {'button'})
        if not accent:
            accent = top_color_for('text', {'link'})

        accent_hover = None
        if accent:
            for color in top_colors_for('background', {'button'}, limit=3):
                if color != accent:
                    accent_hover = color
                    break

        bot_bubble_bg = top_color_for('background', {'container'}) or widget_bg
        user_bubble_bg = accent or top_color_for('background', {'link'})
        user_bubble_text = None
        if user_bubble_bg:
            user_bubble_text = '#ffffff' if self._is_dark_color(user_bubble_bg) else '#000000'

        return {
            'widgetBg': widget_bg,
            'border': border,
            'textPrimary': text_primary,
            'textMuted': text_muted,
            'accent': accent,
            'accentHover': accent_hover,
            'botBubbleBg': bot_bubble_bg,
            'userBubbleBg': user_bubble_bg,
            'userBubbleText': user_bubble_text
        }

    def _normalize_computed_color(self, color_str: Optional[str]) -> Optional[str]:
        """Normalize computed color and filter transparent/garbage values"""
        if not color_str:
            return None

        lowered = color_str.strip().lower()
        if 'var(--tw-' in lowered:
            return None

        if lowered in ['transparent', 'none', 'initial', 'inherit', 'unset']:
            return None

        if self._is_fully_transparent(lowered):
            return None

        return ColorNormalizer.normalize_color(lowered)

    @staticmethod
    def _is_fully_transparent(color_str: str) -> bool:
        """Return True if the color string is fully transparent"""
        rgba_match = re.match(r'rgba\s*\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\s*\)', color_str)
        if rgba_match:
            try:
                return float(rgba_match.group(1)) <= 0
            except ValueError:
                return False

        if color_str.startswith('#'):
            hex_color = color_str.lstrip('#')
            if len(hex_color) == 4:
                return hex_color[3] == '0'
            if len(hex_color) == 8:
                return hex_color[6:8] == '00'

        return False

    @staticmethod
    def _safe_float(value: Optional[str]) -> float:
        try:
            return float(str(value).replace('px', '').strip())
        except Exception:
            return 0.0

    @staticmethod
    def _is_dark_color(hex_color: str) -> bool:
        """Return True if color is dark based on luminance"""
        if not hex_color:
            return False
        try:
            return ColorNormalizer.calculate_luminance(hex_color) < 0.5
        except Exception:
            return False
    
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
    
    def __init__(self, url: str, colors: Dict, colors_by_category: Dict, fonts: Dict, css_variables: Dict,
                 computed_samples: Optional[List[Dict]] = None, ranked_colors: Optional[Dict] = None,
                 tokens: Optional[Dict] = None):
        self.url = url
        self.colors = colors
        self.colors_by_category = colors_by_category
        self.fonts = fonts
        self.css_variables = css_variables
        self.computed_samples = computed_samples or []
        self.ranked_colors = ranked_colors or {}
        self.tokens = tokens or {}
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'total_unique_colors': len(self.colors),
            'total_unique_fonts': len(self.fonts),
            'total_css_variables': len(self.css_variables),
            'total_computed_samples': len(self.computed_samples),
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
            'css_variables': self.css_variables,
            'computed_samples': self.computed_samples,
            'ranked_colors': self.ranked_colors,
            'tokens': self.tokens,
            'widgetTheme': self.tokens
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
        print(f"Computed samples: {summary['total_computed_samples']}")

        # Ranked colors
        if self.ranked_colors:
            print("\n--- RANKED COLORS (VISUAL IMPACT) ---")
            for role, items in self.ranked_colors.items():
                print(f"\n{role.upper()}:")
                for item in items[:5]:
                    print(f"  • {item['color']} | score: {item['score']:.2f} | count: {item['occurrence_count']}")

        # Tokens
        if self.tokens:
            print("\n--- INFERRED TOKENS ---")
            print(f"widgetBg: {self.tokens.get('widgetBg')}")
            print(f"textPrimary: {self.tokens.get('textPrimary')}")
            print(f"accent: {self.tokens.get('accent')}")
            print(f"widgetTheme: {self.tokens}")
        
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
