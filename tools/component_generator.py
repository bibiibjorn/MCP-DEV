
```python
"""
Component Generator
Generates HTML/CSS code from component metadata
"""

import json

class ComponentGenerator:
    def __init__(self, metadata_path):
        with open(metadata_path) as f:
            self.metadata = json.load(f)
    
    def generate_kpi_card(self, data, variant='standard'):
        """Generate KPI card HTML"""
        templates = {
            'standard': '''

    {label}
    {value}
    
        
        {delta_text}
    
    
        
        
    
''',
            'nested': '''

    {label}
    {value}
    {subtitle}
    
        {sub_metrics}
    
'''
        }
        
        template = templates.get(variant, templates['standard'])
        return template.format(**data)
    
    def generate_table(self, data, variant='hierarchical'):
        """Generate table HTML"""
        # Implementation here
        pass
    
    def generate_dashboard(self, config):
        """Generate complete dashboard from config"""
        html_parts = ['', '', '']
        
        # Head section
        html_parts.append('')
        html_parts.append('')
        html_parts.append(f'{config["title"]}')
        html_parts.append('')
        
        # CSS
        html_parts.append('')
        html_parts.append(self._get_base_styles())
        
        for component in config['components']:
            html_parts.append(self._get_component_styles(component))
        
        html_parts.append('')
        html_parts.append('')
        
        # Body
        html_parts.append('')
        html_parts.append('')
        
        for component in config['components']:
            html_parts.append(self._generate_component(component))
        
        html_parts.append('')
        html_parts.append('lucide.createIcons();')
        html_parts.append('')
        html_parts.append('')
        
        return '\n'.join(html_parts)
    
    def _get_base_styles(self):
        """Get base CSS styles"""
        return '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #F8FAFC;
            padding: 24px;
            font-feature-settings: "tnum" 1;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        '''
    
    def _get_component_styles(self, component):
        """Get component-specific CSS"""
        # Load from library
        pass
    
    def _generate_component(self, component):
        """Generate individual component HTML"""
        component_type = component['type']
        
        if component_type == 'kpi-card':
            return self.generate_kpi_card(component['data'], component.get('variant', 'standard'))
        elif component_type == 'table':
            return self.generate_table(component['data'], component.get('variant', 'hierarchical'))
        # ... more component types
        
        return ''

# Usage
if __name__ == '__main__':
    generator = ComponentGenerator('docs/component_metadata.json')
    
    # Example config
    config = {
        'title': 'Executive Dashboard',
        'theme': 'light',
        'components': [
            {
                'type': 'kpi-card',
                'variant': 'standard',
                'data': {
                    'label': 'Total Revenue',
                    'value': '$1.36M',
                    'delta_class': 'positive',
                    'delta_icon': 'trending-up',
                    'delta_text': '+12.4% vs PY',
                    'sparkline_path': 'M 0,24 Q 10,20 20,16...',
                    'sparkline_color': '#3B82F6',
                    'sparkline_fill': 'rgba(59,130,246,0.1)'
                }
            }
        ]
    }
    
    html = generator.generate_dashboard(config)
    
    with open('generated_dashboard.html', 'w') as f:
        f.write(html)
```