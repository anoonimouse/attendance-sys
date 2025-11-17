#!/usr/bin/env python3
"""
Check if all blueprints and routes are properly registered
"""

from app import create_app

app = create_app()

print("\n" + "="*80)
print("BLUEPRINT & ROUTE DIAGNOSTIC")
print("="*80 + "\n")

# Check blueprints
print("📦 REGISTERED BLUEPRINTS:")
print("-" * 80)
for name, blueprint in app.blueprints.items():
    prefix = blueprint.url_prefix or "/"
    print(f"  ✓ {name:<20} URL Prefix: {prefix}")

print("\n" + "="*80)
print("🔗 ALL REGISTERED ROUTES:")
print("="*80 + "\n")

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
        'path': rule.rule
    })

# Sort by endpoint
routes.sort(key=lambda x: x['endpoint'])

# Group by blueprint
current_blueprint = None
for route in routes:
    blueprint_name = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'static'
    
    if blueprint_name != current_blueprint:
        current_blueprint = blueprint_name
        print(f"\n[{current_blueprint.upper()}]")
        print("-" * 80)
    
    print(f"  {route['methods']:<15} {route['path']:<40} -> {route['endpoint']}")

print("\n" + "="*80)

# Check specifically for teacher routes
print("\n🔍 CHECKING TEACHER ROUTES:")
print("-" * 80)
teacher_routes = [r for r in routes if r['endpoint'].startswith('teacher.')]

if teacher_routes:
    print(f"✅ Found {len(teacher_routes)} teacher routes:")
    for route in teacher_routes:
        print(f"  ✓ {route['path']:<40} -> {route['endpoint']}")
else:
    print("❌ NO TEACHER ROUTES FOUND!")
    print("\n🔧 TROUBLESHOOTING:")
    print("  1. Check that teacher_bp is imported in app/__init__.py")
    print("  2. Check that teacher_bp is registered: app.register_blueprint(teacher_bp, url_prefix='/teacher')")
    print("  3. Check that teacher.py has: teacher_bp = Blueprint('teacher', __name__)")
    print("  4. Restart the Flask server")

print("\n" + "="*80)

# Check for teacher.dashboard specifically
teacher_dashboard_exists = any(
    r['endpoint'] == 'teacher.dashboard' for r in routes
)

if teacher_dashboard_exists:
    print("\n✅ teacher.dashboard route EXISTS")
    teacher_dashboard = next(r for r in routes if r['endpoint'] == 'teacher.dashboard')
    print(f"   URL: {teacher_dashboard['path']}")
    print(f"   Methods: {teacher_dashboard['methods']}")
else:
    print("\n❌ teacher.dashboard route DOES NOT EXIST")
    print("\n🔧 CHECK:")
    print("   1. Does teacher.py have @teacher_bp.route('/dashboard') ?")
    print("   2. Is the function named 'dashboard()' ?")
    print("   3. Is teacher_bp properly registered?")

print("\n" + "="*80 + "\n")