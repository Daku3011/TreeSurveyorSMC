from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models.tree import Tree, TreeSpecies, MaintenanceLog
from extensions import db
from datetime import datetime
import os, uuid
from werkzeug.utils import secure_filename

user_bp = Blueprint('user', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(file, folder='trees'):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))
        return f'uploads/{folder}/{filename}'
    return None

def generate_tree_id(zone):
    zone_code = ''.join([c for c in zone if c.isupper()])[:2] or zone[:2].upper()
    count = Tree.query.filter(Tree.zone == zone).count() + 1
    return f"SMC-{zone_code}-{count:05d}"

def to_float_or_none(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return None

def to_int_or_none(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        return int(float(val_str))
    except (ValueError, TypeError):
        return None

@user_bp.route('/dashboard')
@login_required
def dashboard():
    my_trees = Tree.query.filter_by(surveyed_by=current_user.id, status='active').count()
    recent_trees = Tree.query.filter_by(surveyed_by=current_user.id).order_by(
        Tree.survey_date.desc()).limit(5).all()
    
    zone_trees = Tree.query.filter_by(
        zone=current_user.zone, status='active').count() if current_user.zone else 0
    
    # My trees health distribution
    health_dist = db.session.query(
        Tree.health_condition, db.func.count(Tree.id)
    ).filter_by(surveyed_by=current_user.id, status='active').group_by(Tree.health_condition).all()
    
    return render_template('user/dashboard.html',
        my_trees=my_trees,
        recent_trees=recent_trees,
        zone_trees=zone_trees,
        health_dist=health_dist
    )

@user_bp.route('/add-tree', methods=['GET', 'POST'])
@login_required
def add_tree():
    species_list = TreeSpecies.query.order_by(TreeSpecies.common_name_english).all()
    
    if request.method == 'POST':
        f = request.form
        
        # Validate GPS
        try:
            lat = float(f.get('latitude'))
            lng = float(f.get('longitude'))
        except (TypeError, ValueError):
            flash('Valid GPS coordinates required.', 'danger')
            return render_template('user/add_tree.html', species_list=species_list)
        
        zone = f.get('zone', current_user.zone or 'Central Zone')
        tree_id = generate_tree_id(zone)
        
        # Handle photo uploads
        photo_main = save_photo(request.files.get('photo_main'))
        photo_bark = save_photo(request.files.get('photo_bark'))
        photo_leaf = save_photo(request.files.get('photo_leaf'))
        photo_canopy = save_photo(request.files.get('photo_canopy'))
        
        # Safely convert numeric fields
        altitude = to_float_or_none(f.get('altitude'))
        gps_accuracy = to_float_or_none(f.get('gps_accuracy'))
        tree_height = to_float_or_none(f.get('tree_height'))
        trunk_girth = to_float_or_none(f.get('trunk_girth'))
        canopy_spread_ns = to_float_or_none(f.get('canopy_spread_ns'))
        canopy_spread_ew = to_float_or_none(f.get('canopy_spread_ew'))
        dbh = to_float_or_none(f.get('dbh'))
        estimated_age = to_int_or_none(f.get('estimated_age'))
        
        # Calculate carbon stock (simplified formula)
        if dbh and tree_height:
            agb = 0.0509 * (dbh ** 2) * tree_height
            carbon = round(agb * 0.5, 2)
        else:
            carbon = 0.0
        
        tree = Tree(
            tree_id=tree_id,
            latitude=lat,
            longitude=lng,
            altitude=altitude,
            gps_accuracy=gps_accuracy,
            zone=zone,
            ward=f.get('ward', current_user.ward),
            ward_number=f.get('ward_number'),
            area_name=f.get('area_name'),
            street_address=f.get('street_address'),
            location_type=f.get('location_type'),
            common_name_gujarati=f.get('common_name_gujarati'),
            common_name_english=f.get('common_name_english'),
            botanical_name=f.get('botanical_name'),
            family=f.get('family'),
            tree_height=tree_height,
            trunk_girth=trunk_girth,
            canopy_spread_ns=canopy_spread_ns,
            canopy_spread_ew=canopy_spread_ew,
            dbh=dbh,
            health_condition=f.get('health_condition'),
            structural_condition=f.get('structural_condition'),
            pest_disease=f.get('pest_disease'),
            damage_type=f.get('damage_type'),
            estimated_age=estimated_age,
            growth_stage=f.get('growth_stage'),
            soil_type=f.get('soil_type'),
            water_availability=f.get('water_availability'),
            tree_guard=f.get('tree_guard') == 'on',
            tree_tag_number=f.get('tree_tag_number'),
            carbon_stock=carbon,
            oxygen_production=round(carbon * 2.67, 2) if carbon else 0.0,
            ecological_value=f.get('ecological_value'),
            action_required=f.get('action_required'),
            priority=f.get('priority'),
            photo_main=photo_main,
            photo_bark=photo_bark,
            photo_leaf=photo_leaf,
            photo_canopy=photo_canopy,
            ai_description=f.get('ai_description'),
            ai_confidence=f.get('ai_confidence'),
            ai_ecological_notes=f.get('ai_ecological_notes'),
            surveyed_by=current_user.id,
            notes=f.get('notes'),
            status='active'
        )
        
        db.session.add(tree)
        db.session.commit()
        
        flash(f'Tree {tree_id} added successfully!', 'success')
        return redirect(url_for('user.tree_detail', tree_id=tree.id))
    
    smc_zones = [
        'Central Zone', 'East Zone', 'West Zone', 
        'North Zone', 'South Zone', 'South-West Zone'
    ]
    return render_template('user/add_tree.html', species_list=species_list, zones=smc_zones)

@user_bp.route('/trees')
@login_required
def my_trees():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Tree.query.filter_by(surveyed_by=current_user.id)
    if search:
        query = query.filter(
            db.or_(
                Tree.tree_id.ilike(f'%{search}%'),
                Tree.common_name_english.ilike(f'%{search}%'),
                Tree.area_name.ilike(f'%{search}%')
            )
        )
    
    trees = query.order_by(Tree.survey_date.desc()).paginate(page=page, per_page=20)
    return render_template('user/trees.html', trees=trees, search=search)

@user_bp.route('/trees/<int:tree_id>')
@login_required
def tree_detail(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    maintenance = MaintenanceLog.query.filter_by(tree_id=tree_id).order_by(
        MaintenanceLog.action_date.desc()).all()
    return render_template('user/tree_detail.html', tree=tree, maintenance=maintenance)

@user_bp.route('/trees/<int:tree_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tree(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    
    if tree.surveyed_by != current_user.id and current_user.role != 'admin':
        flash('You can only edit your own entries.', 'danger')
        return redirect(url_for('user.my_trees'))
    
    species_list = TreeSpecies.query.order_by(TreeSpecies.common_name_english).all()
    
    if request.method == 'POST':
        f = request.form
        
        lat = to_float_or_none(f.get('latitude'))
        if lat is not None:
            tree.latitude = lat
        lng = to_float_or_none(f.get('longitude'))
        if lng is not None:
            tree.longitude = lng
        tree.area_name = f.get('area_name', tree.area_name)
        tree.street_address = f.get('street_address', tree.street_address)
        tree.common_name_gujarati = f.get('common_name_gujarati', tree.common_name_gujarati)
        tree.common_name_english = f.get('common_name_english', tree.common_name_english)
        tree.botanical_name = f.get('botanical_name', tree.botanical_name)
        if f.get('tree_height') is not None:
            tree.tree_height = to_float_or_none(f.get('tree_height'))
        if f.get('trunk_girth') is not None:
            tree.trunk_girth = to_float_or_none(f.get('trunk_girth'))
        tree.health_condition = f.get('health_condition', tree.health_condition)
        tree.action_required = f.get('action_required', tree.action_required)
        tree.notes = f.get('notes', tree.notes)
        if f.get('ai_description'):
            tree.ai_description = f.get('ai_description')
        if f.get('ai_confidence'):
            tree.ai_confidence = f.get('ai_confidence')
        if f.get('ai_ecological_notes'):
            tree.ai_ecological_notes = f.get('ai_ecological_notes')
        tree.last_updated = datetime.utcnow()
        
        if request.files.get('photo_main'):
            tree.photo_main = save_photo(request.files.get('photo_main'))
        
        db.session.commit()
        flash('Tree updated successfully!', 'success')
        return redirect(url_for('user.tree_detail', tree_id=tree_id))
    
    return render_template('user/edit_tree.html', tree=tree, species_list=species_list)

@user_bp.route('/map')
@login_required
def map_view():
    return render_template('user/map.html')

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.zone = request.form.get('zone', current_user.zone)
        current_user.ward = request.form.get('ward', current_user.ward)
        
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Password changed successfully.', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('user/profile.html')
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    
    return render_template('user/profile.html')