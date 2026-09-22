from extensions import db
from datetime import datetime
import json

class Tree(db.Model):
    __tablename__ = 'trees'
    
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g., SMC-Z1-00001
    
    # Location Details
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float)
    gps_accuracy = db.Column(db.Float)  # in meters
    
    # Administrative Location
    zone = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.String(100))
    ward_number = db.Column(db.String(20))
    area_name = db.Column(db.String(200))
    street_address = db.Column(db.String(500))
    location_type = db.Column(db.String(100))  # Road, Park, Garden, School, Hospital, etc.
    
    # Tree Identification
    common_name_gujarati = db.Column(db.String(200))
    common_name_english = db.Column(db.String(200))
    botanical_name = db.Column(db.String(200))
    family = db.Column(db.String(200))
    
    # Tree Physical Details
    tree_height = db.Column(db.Float)  # in meters
    trunk_girth = db.Column(db.Float)  # circumference in cm at breast height (1.3m)
    canopy_spread_ns = db.Column(db.Float)  # North-South in meters
    canopy_spread_ew = db.Column(db.Float)  # East-West in meters
    dbh = db.Column(db.Float)  # Diameter at Breast Height in cm
    
    # Tree Health & Condition
    health_condition = db.Column(db.String(50))  # Excellent, Good, Fair, Poor, Dead
    structural_condition = db.Column(db.String(50))  # Safe, Moderate Risk, High Risk
    pest_disease = db.Column(db.String(500))
    damage_type = db.Column(db.String(500))
    
    # Tree Age & Growth
    estimated_age = db.Column(db.Integer)  # in years
    growth_stage = db.Column(db.String(50))  # Sapling, Young, Mature, Old
    
    # Environmental Details
    soil_type = db.Column(db.String(100))
    water_availability = db.Column(db.String(100))
    tree_guard = db.Column(db.Boolean, default=False)
    tree_tag_number = db.Column(db.String(50))
    
    # Carbon & Ecological Value
    carbon_stock = db.Column(db.Float)  # kg CO2
    oxygen_production = db.Column(db.Float)  # kg per year
    ecological_value = db.Column(db.String(50))  # High, Medium, Low
    
    # Action Required
    action_required = db.Column(db.String(200))  # Pruning, Treatment, Removal, None
    priority = db.Column(db.String(20))  # High, Medium, Low
    
    # Images
    photo_main = db.Column(db.String(500))
    photo_bark = db.Column(db.String(500))
    photo_leaf = db.Column(db.String(500))
    photo_canopy = db.Column(db.String(500))
    
    # QR Code
    qr_code = db.Column(db.String(500))
    
    # AI Analysis
    ai_description = db.Column(db.Text)  # AI-generated tree description
    ai_confidence = db.Column(db.String(20))  # High, Medium, Low
    ai_ecological_notes = db.Column(db.Text)  # AI ecological assessment
    
    # Metadata
    surveyed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    survey_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, removed, dead
    notes = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tree_id': self.tree_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'common_name_english': self.common_name_english,
            'common_name_gujarati': self.common_name_gujarati,
            'botanical_name': self.botanical_name,
            'zone': self.zone,
            'ward': self.ward,
            'area_name': self.area_name,
            'health_condition': self.health_condition,
            'tree_height': self.tree_height,
            'status': self.status,
            'survey_date': self.survey_date.isoformat() if self.survey_date else None,
            'photo_main': self.photo_main,
            'is_verified': self.is_verified,
            'ai_description': self.ai_description,
            'ai_confidence': self.ai_confidence,
            'ai_ecological_notes': self.ai_ecological_notes
        }
    
    def __repr__(self):
        return f'<Tree {self.tree_id}>'


class TreeSpecies(db.Model):
    __tablename__ = 'tree_species'
    
    id = db.Column(db.Integer, primary_key=True)
    common_name_gujarati = db.Column(db.String(200))
    common_name_english = db.Column(db.String(200), nullable=False)
    botanical_name = db.Column(db.String(200))
    family = db.Column(db.String(200))
    native = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Species {self.common_name_english}>'


class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(db.Integer, db.ForeignKey('trees.id'), nullable=False)
    action_type = db.Column(db.String(100))  # Pruning, Treatment, Watering, Removal
    action_date = db.Column(db.DateTime, default=datetime.utcnow)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    cost = db.Column(db.Float)
    before_photo = db.Column(db.String(500))
    after_photo = db.Column(db.String(500))
    
    tree = db.relationship('Tree', backref='maintenance_logs')
    worker = db.relationship('User', foreign_keys=[performed_by])
    
    def __repr__(self):
        return f'<MaintenanceLog {self.id}>'
