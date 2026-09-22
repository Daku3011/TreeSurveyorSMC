from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models.tree import Tree, TreeSpecies
from extensions import db
from werkzeug.utils import secure_filename
import os
import uuid

api_bp = Blueprint('api', __name__)

@api_bp.route('/trees/geojson')
@login_required
def trees_geojson():
    """Return all trees as GeoJSON for map display"""
    zone = request.args.get('zone', '')
    health = request.args.get('health', '')
    
    query = Tree.query.filter_by(status='active')
    if zone:
        query = query.filter_by(zone=zone)
    if health:
        query = query.filter_by(health_condition=health)
    
    # Limit to user's zone if not admin
    if current_user.role != 'admin' and current_user.zone:
        query = query.filter_by(zone=current_user.zone)
    
    trees = query.all()
    
    features = []
    for tree in trees:
        health_color = {
            'Excellent': '#22c55e',
            'Good': '#84cc16',
            'Fair': '#f59e0b',
            'Poor': '#ef4444',
            'Dead': '#6b7280'
        }.get(tree.health_condition, '#3b82f6')
        
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [tree.longitude, tree.latitude]
            },
            'properties': {
                'id': tree.id,
                'tree_id': tree.tree_id,
                'name_gu': tree.common_name_gujarati or '',
                'name_en': tree.common_name_english or '',
                'botanical': tree.botanical_name or '',
                'zone': tree.zone,
                'ward': tree.ward or '',
                'area': tree.area_name or '',
                'health': tree.health_condition or '',
                'height': tree.tree_height,
                'girth': tree.trunk_girth,
                'age': tree.estimated_age,
                'carbon': tree.carbon_stock,
                'color': health_color,
                'verified': tree.is_verified,
                'photo': f'/static/{tree.photo_main}' if tree.photo_main else None,
                'survey_date': tree.survey_date.strftime('%d/%m/%Y') if tree.survey_date else ''
            }
        })
    
    return jsonify({
        'type': 'FeatureCollection',
        'features': features,
        'total': len(features)
    })

@api_bp.route('/trees/<int:tree_id>')
@login_required
def tree_api(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    return jsonify(tree.to_dict())

@api_bp.route('/stats')
@login_required
def stats():
    total = Tree.query.filter_by(status='active').count()
    
    health_data = db.session.query(
        Tree.health_condition, db.func.count(Tree.id)
    ).filter_by(status='active').group_by(Tree.health_condition).all()
    
    zone_data = db.session.query(
        Tree.zone, db.func.count(Tree.id)
    ).filter_by(status='active').group_by(Tree.zone).all()
    
    carbon = db.session.query(db.func.sum(Tree.carbon_stock)).filter_by(status='active').scalar() or 0
    
    return jsonify({
        'total_trees': total,
        'health': {h: c for h, c in health_data},
        'zones': {z: c for z, c in zone_data},
        'total_carbon_kg': round(carbon, 2)
    })

@api_bp.route('/species')
@login_required
def species_list():
    species = TreeSpecies.query.order_by(TreeSpecies.common_name_english).all()
    return jsonify([{
        'id': s.id,
        'gujarati': s.common_name_gujarati,
        'english': s.common_name_english,
        'botanical': s.botanical_name,
        'family': s.family
    } for s in species])

@api_bp.route('/zones')
@login_required
def zones():
    smc_zones = [
        'Central Zone', 'East Zone', 'West Zone',
        'North Zone', 'South Zone', 'South-West Zone'
    ]
    return jsonify(smc_zones)

@api_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    trees = Tree.query.filter(
        db.or_(
            Tree.tree_id.ilike(f'%{q}%'),
            Tree.common_name_english.ilike(f'%{q}%'),
            Tree.common_name_gujarati.ilike(f'%{q}%'),
            Tree.area_name.ilike(f'%{q}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': t.id,
        'tree_id': t.tree_id,
        'name': f"{t.common_name_gujarati} / {t.common_name_english}",
        'area': t.area_name,
        'lat': t.latitude,
        'lng': t.longitude
    } for t in trees])

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@api_bp.route('/ai/analyze-tree', methods=['POST'])
@login_required
def ai_analyze_tree():
    """Analyze an uploaded tree image using AI (Google Gemini Vision).
    
    Accepts a multipart form with an 'image' file field.
    Returns JSON with species identification, health assessment, and description.
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_image(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Use PNG, JPG, or WebP'}), 400
    
    # Save temporarily for analysis
    filename = secure_filename(f"ai_temp_{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}")
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ai_temp')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    
    try:
        file.save(filepath)
        
        from services.ai_service import analyze_tree_image
        result = analyze_tree_image(filepath)
        
        return jsonify(result)
        
    except ValueError as e:
        # Missing API key
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'}), 500
    finally:
        # Clean up temp file
        if os.path.exists(filepath):
            os.remove(filepath)
