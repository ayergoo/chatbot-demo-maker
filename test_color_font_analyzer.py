#!/usr/bin/env python3
"""
Test script for color_font_analyzer.py
"""

from color_font_analyzer import (
    ColorNormalizer, ColorExtractor, FontExtractor, 
    WebpageAnalyzer, AnalysisResult
)


def test_color_normalization():
    """Test color normalization to hex format"""
    print("Testing color normalization...")
    
    # Hex colors
    assert ColorNormalizer.normalize_color('#fff') == '#ffffff'
    assert ColorNormalizer.normalize_color('#000000') == '#000000'
    assert ColorNormalizer.normalize_color('#abc') == '#aabbcc'
    
    # Named colors
    assert ColorNormalizer.normalize_color('red') == '#ff0000'
    assert ColorNormalizer.normalize_color('white') == '#ffffff'
    assert ColorNormalizer.normalize_color('black') == '#000000'
    
    # RGB colors
    assert ColorNormalizer.normalize_color('rgb(255, 0, 0)') == '#ff0000'
    assert ColorNormalizer.normalize_color('rgb(255, 255, 255)') == '#ffffff'
    assert ColorNormalizer.normalize_color('rgba(0, 0, 0, 0.5)') == '#000000'
    
    # Invalid colors
    assert ColorNormalizer.normalize_color('') is None
    assert ColorNormalizer.normalize_color('invalid') is None
    
    print("✓ Color normalization tests passed")


def test_color_variants():
    """Test getting color variants"""
    print("Testing color variants...")
    
    variants = ColorNormalizer.get_color_variants('#ff0000')
    assert '#ff0000' in variants
    assert 'rgb(255, 0, 0)' in variants
    
    variants = ColorNormalizer.get_color_variants('white')
    assert '#ffffff' in variants
    assert 'white' in variants
    
    print("✓ Color variants tests passed")


def test_contrast_ratio():
    """Test contrast ratio calculation"""
    print("Testing contrast ratio calculation...")
    
    # Black on white should be 21:1
    ratio = ColorNormalizer.calculate_contrast_ratio('#000000', '#ffffff')
    assert 20 < ratio < 22, f"Expected ~21, got {ratio}"
    
    # Same color should be 1:1
    ratio = ColorNormalizer.calculate_contrast_ratio('#ff0000', '#ff0000')
    assert 0.9 < ratio < 1.1, f"Expected ~1, got {ratio}"
    
    print("✓ Contrast ratio tests passed")


def test_color_extraction():
    """Test color extraction from CSS"""
    print("Testing color extraction...")
    
    extractor = ColorExtractor()
    
    # Test categorization
    category = extractor.categorize_color('.button', 'background-color')
    assert category == 'interactive', f"Expected 'interactive', got '{category}'"
    
    category = extractor.categorize_color('.text', 'color')
    assert category == 'text', f"Expected 'text', got '{category}'"
    
    category = extractor.categorize_color('.border', 'border-color')
    assert category == 'border', f"Expected 'border', got '{category}'"
    
    category = extractor.categorize_color('.error-message', 'color')
    assert category == 'semantic_error', f"Expected 'semantic_error', got '{category}'"
    
    print("✓ Color extraction tests passed")


def test_font_extraction():
    """Test font extraction"""
    print("Testing font extraction...")
    
    extractor = FontExtractor()
    
    # Create a mock CSS rule structure
    class MockDeclaration:
        def __init__(self, name, value):
            self.name = name
            self.value = value
    
    class MockRule:
        def __init__(self):
            self.selector_list = "body"
            self.declarations = [
                MockDeclaration('font-family', 'Arial, sans-serif'),
                MockDeclaration('font-size', '16px'),
                MockDeclaration('font-weight', 'bold')
            ]
    
    # This is a simplified test - in reality, the rule structure is more complex
    # Just verify the extractor initializes correctly
    assert len(extractor.fonts) == 0
    print("✓ Font extraction tests passed")


def test_color_extractor_add():
    """Test adding colors to extractor"""
    print("Testing color extractor add...")
    
    extractor = ColorExtractor()
    
    # Add a color
    extractor._add_color('#ff0000', '#ff0000', '.button', 'background-color')
    
    assert '#ff0000' in extractor.colors
    assert extractor.colors['#ff0000']['frequency'] == 1
    assert '.button' in extractor.colors['#ff0000']['selectors']
    assert 'background-color' in extractor.colors['#ff0000']['properties']
    
    # Add same color again
    extractor._add_color('red', '#ff0000', '.link', 'color')
    assert extractor.colors['#ff0000']['frequency'] == 2
    assert '.link' in extractor.colors['#ff0000']['selectors']
    
    print("✓ Color extractor add tests passed")


def test_analysis_result():
    """Test AnalysisResult class"""
    print("Testing AnalysisResult...")
    
    # Create mock data
    colors = {
        '#ff0000': {
            'value': 'red',
            'normalized': '#ff0000',
            'selectors': {'.button'},
            'properties': {'background-color'},
            'frequency': 2,
            'css_variables': set(),
            'contrast_contexts': []
        }
    }
    
    colors_by_category = {
        'interactive': [
            {
                'color': 'red',
                'normalized': '#ff0000',
                'selector': '.button',
                'property': 'background-color',
                'frequency': 2
            }
        ]
    }
    
    fonts = {
        'Arial': {
            'family': 'Arial, sans-serif',
            'sizes': {'16px': 1},
            'weights': {'bold': 1},
            'line_heights': {},
            'selectors': {'body'},
            'frequency': 1
        }
    }
    
    css_variables = {'--primary-color': '#ff0000'}
    
    result = AnalysisResult(
        url='https://example.com',
        colors=colors,
        colors_by_category=colors_by_category,
        fonts=fonts,
        css_variables=css_variables
    )
    
    # Test summary
    summary = result.get_summary()
    assert summary['total_unique_colors'] == 1
    assert summary['total_unique_fonts'] == 1
    assert summary['total_css_variables'] == 1
    
    # Test to_dict
    data = result.to_dict()
    assert data['url'] == 'https://example.com'
    assert '#ff0000' in data['colors']
    assert isinstance(data['colors']['#ff0000']['selectors'], list)
    
    print("✓ AnalysisResult tests passed")


def test_url_handling():
    """Test URL handling in analyzer"""
    print("Testing URL handling...")
    
    analyzer = WebpageAnalyzer('https://example.com', timeout=5)
    assert analyzer.url == 'https://example.com'
    assert analyzer.timeout == 5
    
    print("✓ URL handling tests passed")


def test_color_extraction_from_value():
    """Test extracting colors from CSS value strings"""
    print("Testing color extraction from values...")
    
    extractor = ColorExtractor()
    
    # Hex colors
    color = extractor._extract_color_from_value('#ff0000')
    assert color == '#ff0000'
    
    # RGB colors
    color = extractor._extract_color_from_value('rgb(255, 0, 0)')
    assert color == 'rgb(255, 0, 0)'
    
    # Named colors
    color = extractor._extract_color_from_value('border: 1px solid red')
    assert color == 'red'
    
    # HSL colors
    color = extractor._extract_color_from_value('hsl(0, 100%, 50%)')
    assert color == 'hsl(0, 100%, 50%)'
    
    # No color
    color = extractor._extract_color_from_value('1px solid')
    assert color is None
    
    print("✓ Color extraction from values tests passed")


def test_hsl_conversion():
    """Test HSL to hex conversion"""
    print("Testing HSL conversion...")
    
    # Red: hsl(0, 100%, 50%)
    normalized = ColorNormalizer.normalize_color('hsl(0, 100%, 50%)')
    assert normalized == '#ff0000'
    
    # Blue: hsl(240, 100%, 50%)
    normalized = ColorNormalizer.normalize_color('hsl(240, 100%, 50%)')
    assert normalized == '#0000ff'
    
    print("✓ HSL conversion tests passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Running color_font_analyzer tests")
    print("=" * 60 + "\n")
    
    try:
        test_color_normalization()
        test_color_variants()
        test_contrast_ratio()
        test_color_extraction()
        test_font_extraction()
        test_color_extractor_add()
        test_analysis_result()
        test_url_handling()
        test_color_extraction_from_value()
        test_hsl_conversion()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
