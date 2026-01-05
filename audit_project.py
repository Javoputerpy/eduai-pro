import os
import re

def find_html_files(directory):
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))
    return html_files

def extract_url_endpoints(file_path):
    endpoints = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Regex for url_for('endpoint_name') or url_for("endpoint_name")
            matches = re.findall(r"url_for\s*\(\s*['\"]([^'\"]+)['\"]", content)
            for match in matches:
                # exclude static file references
                if match != 'static':
                    endpoints.append((match, file_path))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return endpoints

def extract_app_routes(app_file):
    defined_endpoints = set()
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Regex to find @app.route followed by def endpoint():
            # This is a simplification; Flask uses function name as endpoint defaults
            
            # Pattern 1: Find all 'def function_name(' that are likely views
            # But simpler: scan for @app.route decorator, then grab the next 'def x'
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    # Check if previous lines were decorators
                    j = i - 1
                    is_route = False
                    while j >= 0:
                        prev = lines[j].strip()
                        if prev.startswith('@app.route') or prev.startswith('@login_required') or prev.startswith('@'):
                            if prev.startswith('@app.route'):
                                is_route = True
                            j -= 1
                        else:
                            break
                    
                    if is_route:
                        func_name = line.strip()[4:].split('(')[0]
                        defined_endpoints.add(func_name)

    except Exception as e:
        print(f"Error reading app file: {e}")
    return defined_endpoints

def audit():
    print("Starting Audit...")
    templates_dir = 'templates'
    app_file = 'app.py'
    
    html_files = find_html_files(templates_dir)
    print(f"Found {len(html_files)} HTML templates.")
    
    all_referenced_endpoints = []
    for html in html_files:
        endpoints = extract_url_endpoints(html)
        all_referenced_endpoints.extend(endpoints)
        
    print(f"Found {len(all_referenced_endpoints)} references to endpoints in templates.")
    
    defined_endpoints = extract_app_routes(app_file)
    print(f"Found {len(defined_endpoints)} defined routes in app.py:\n{sorted(list(defined_endpoints))}")
    
    missing = set()
    for endpoint, file in all_referenced_endpoints:
        if endpoint not in defined_endpoints:
            print(f"MISSING: {endpoint} (referenced in {file})")
            missing.add(endpoint)
            
    if not missing:
        print("\nAll template links appear valid!")
    else:
        print(f"\nTotal Missing Endpoints: {len(missing)}")

if __name__ == "__main__":
    audit()
