from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from models.tree import Tree, TreeSpecies, MaintenanceLog
from models.user import User
from extensions import db
from datetime import datetime, timedelta
from functools import wraps
import os, io
import pandas as pd

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Statistics
    total_trees = Tree.query.filter_by(status='active').count()
    total_users = User.query.filter_by(role='user').count()
    
    zone_stats = db.session.query(
        Tree.zone, db.func.count(Tree.id).label('count')
    ).filter_by(status='active').group_by(Tree.zone).all()
    
    health_stats = db.session.query(
        Tree.health_condition, db.func.count(Tree.id).label('count')
    ).filter_by(status='active').group_by(Tree.health_condition).all()
    
    species_stats = db.session.query(
        Tree.common_name_english, db.func.count(Tree.id).label('count')
    ).filter_by(status='active').group_by(Tree.common_name_english).order_by(
        db.func.count(Tree.id).desc()
    ).limit(10).all()
    
    # Recent activity
    recent_trees = Tree.query.order_by(Tree.survey_date.desc()).limit(10).all()
    pending_verification = Tree.query.filter_by(is_verified=False, status='active').count()
    
    # Monthly survey data (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        date = datetime.utcnow() - timedelta(days=30*i)
        count = Tree.query.filter(
            db.extract('month', Tree.survey_date) == date.month,
            db.extract('year', Tree.survey_date) == date.year
        ).count()
        monthly_data.append({'month': date.strftime('%b %Y'), 'count': count})
    
    return render_template('admin/dashboard.html',
        total_trees=total_trees,
        total_users=total_users,
        zone_stats=zone_stats,
        health_stats=health_stats,
        species_stats=species_stats,
        recent_trees=recent_trees,
        pending_verification=pending_verification,
        monthly_data=monthly_data
    )

@admin_bp.route('/trees')
@login_required
@admin_required
def tree_list():
    page = request.args.get('page', 1, type=int)
    zone = request.args.get('zone', '')
    health = request.args.get('health', '')
    search = request.args.get('search', '')
    
    query = Tree.query
    if zone:
        query = query.filter_by(zone=zone)
    if health:
        query = query.filter_by(health_condition=health)
    if search:
        query = query.filter(
            db.or_(
                Tree.tree_id.ilike(f'%{search}%'),
                Tree.common_name_english.ilike(f'%{search}%'),
                Tree.common_name_gujarati.ilike(f'%{search}%'),
                Tree.area_name.ilike(f'%{search}%')
            )
        )
    
    trees = query.order_by(Tree.survey_date.desc()).paginate(page=page, per_page=25)
    zones = db.session.query(Tree.zone).distinct().all()
    
    return render_template('admin/trees.html', trees=trees, zones=zones, 
                          selected_zone=zone, selected_health=health, search=search)

@admin_bp.route('/trees/<int:tree_id>')
@login_required
@admin_required
def tree_detail(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    maintenance = MaintenanceLog.query.filter_by(tree_id=tree_id).order_by(MaintenanceLog.action_date.desc()).all()
    return render_template('admin/tree_detail.html', tree=tree, maintenance=maintenance)

@admin_bp.route('/trees/<int:tree_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_tree(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    tree.is_verified = True
    tree.verified_by = current_user.id
    tree.verified_at = datetime.utcnow()
    db.session.commit()
    flash(f'Tree {tree.tree_id} verified successfully!', 'success')
    return redirect(url_for('admin.tree_detail', tree_id=tree_id))

@admin_bp.route('/trees/<int:tree_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_tree(tree_id):
    tree = Tree.query.get_or_404(tree_id)
    tree.status = 'removed'
    db.session.commit()
    flash(f'Tree {tree.tree_id} marked as removed.', 'warning')
    return redirect(url_for('admin.tree_list'))

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/map')
@login_required
@admin_required
def map_view():
    zones = db.session.query(Tree.zone).distinct().all()
    total_trees = Tree.query.filter_by(status='active').count()
    return render_template('admin/map.html', zones=zones, total_trees=total_trees)

@admin_bp.route('/export')
@login_required
@admin_required
def export_trees():
    trees = Tree.query.filter_by(status='active').all()
    
    data = []
    for t in trees:
        data.append({
            'Tree ID': t.tree_id,
            'Gujarati Name': t.common_name_gujarati,
            'English Name': t.common_name_english,
            'Botanical Name': t.botanical_name,
            'Zone': t.zone,
            'Ward': t.ward,
            'Area': t.area_name,
            'Street': t.street_address,
            'Latitude': t.latitude,
            'Longitude': t.longitude,
            'Height (m)': t.tree_height,
            'Girth (cm)': t.trunk_girth,
            'Health': t.health_condition,
            'Age (yrs)': t.estimated_age,
            'Carbon (kg)': t.carbon_stock,
            'Survey Date': t.survey_date.strftime('%Y-%m-%d') if t.survey_date else '',
            'Verified': 'Yes' if t.is_verified else 'No',
            'AI Description': t.ai_description or '',
            'AI Confidence': t.ai_confidence or ''
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='SMC Tree Census', index=False)
    output.seek(0)
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    download_name=f'SMC_Tree_Census_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    as_attachment=True)

@admin_bp.route('/species')
@login_required
@admin_required
def species_list():
    species = TreeSpecies.query.all()
    return render_template('admin/species.html', species=species)

@admin_bp.route('/species/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_species():
    if request.method == 'POST':
        sp = TreeSpecies(
            common_name_gujarati=request.form.get('gujarati_name'),
            common_name_english=request.form.get('english_name'),
            botanical_name=request.form.get('botanical_name'),
            family=request.form.get('family'),
            native=request.form.get('native') == 'on',
            description=request.form.get('description')
        )
        db.session.add(sp)
        db.session.commit()
        flash('Species added successfully!', 'success')
        return redirect(url_for('admin.species_list'))
    return render_template('admin/add_species.html')

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    # Zone-wise report
    zone_report = db.session.query(
        Tree.zone,
        db.func.count(Tree.id).label('total'),
        db.func.sum(db.case((Tree.health_condition == 'Excellent', 1), else_=0)).label('excellent'),
        db.func.sum(db.case((Tree.health_condition == 'Good', 1), else_=0)).label('good'),
        db.func.sum(db.case((Tree.health_condition == 'Fair', 1), else_=0)).label('fair'),
        db.func.sum(db.case((Tree.health_condition == 'Poor', 1), else_=0)).label('poor'),
        db.func.avg(Tree.tree_height).label('avg_height'),
        db.func.sum(Tree.carbon_stock).label('total_carbon')
    ).filter(Tree.status == 'active').group_by(Tree.zone).all()
    
    return render_template('admin/reports.html', zone_report=zone_report)
