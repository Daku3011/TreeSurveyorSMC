"""
SMC Tree Census - Database Seeder
Run: python seed.py
Seeds default species data for Surat region trees
"""
from app import create_app
from extensions import db
from models.user import User
from models.tree import Tree, TreeSpecies
from werkzeug.security import generate_password_hash
from datetime import datetime
import random

app = create_app()

SURAT_SPECIES = [
    # (Gujarati, English, Botanical, Family, Native)
    ("આંબો", "Mango", "Mangifera indica", "Anacardiaceae", True),
    ("વડ", "Banyan", "Ficus benghalensis", "Moraceae", True),
    ("પીપળ", "Sacred Fig / Peepal", "Ficus religiosa", "Moraceae", True),
    ("નીમ", "Neem", "Azadirachta indica", "Meliaceae", True),
    ("ગુલમહોર", "Royal Poinciana", "Delonix regia", "Fabaceae", False),
    ("સાગ", "Teak", "Tectona grandis", "Lamiaceae", True),
    ("બાવળ", "Acacia / Babul", "Acacia nilotica", "Fabaceae", True),
    ("અર્જુન", "Arjun Tree", "Terminalia arjuna", "Combretaceae", True),
    ("જાંબુ", "Indian Blackberry", "Syzygium cumini", "Myrtaceae", True),
    ("ચીકુ", "Sapodilla", "Manilkara zapota", "Sapotaceae", False),
    ("જામફળ", "Guava", "Psidium guajava", "Myrtaceae", False),
    ("આમળા", "Indian Gooseberry", "Phyllanthus emblica", "Phyllanthaceae", True),
    ("બહેડો", "Baheda", "Terminalia bellirica", "Combretaceae", True),
    ("હરડે", "Harad", "Terminalia chebula", "Combretaceae", True),
    ("કદંબ", "Kadamba", "Neolamarckia cadamba", "Rubiaceae", True),
    ("ખીજળો", "Khejri", "Prosopis cineraria", "Fabaceae", True),
    ("ઉંબો", "Cluster Fig", "Ficus racemosa", "Moraceae", True),
    ("સરગવો", "Moringa / Drumstick", "Moringa oleifera", "Moringaceae", True),
    ("કોળો", "Bottle Gourd Tree", "Crescentia cujete", "Bignoniaceae", False),
    ("કાસ", "Golden Shower", "Cassia fistula", "Fabaceae", True),
    ("ટમોટો", "Tamarind", "Tamarindus indica", "Fabaceae", True),
    ("સીમળો", "Silk Cotton", "Bombax ceiba", "Malvaceae", True),
    ("અશોક", "Ashoka", "Saraca asoca", "Fabaceae", True),
    ("ટીળ", "Indian Rosewood", "Dalbergia sissoo", "Fabaceae", True),
    ("ખેર", "Catechu", "Acacia catechu", "Fabaceae", True),
    ("ઓળ", "African Tulip", "Spathodea campanulata", "Bignoniaceae", False),
    ("ગળો", "Guduchi", "Tinospora cordifolia", "Menispermaceae", True),
    ("બોર", "Indian Jujube", "Ziziphus mauritiana", "Rhamnaceae", True),
    ("ટ્રેમ્બ", "Rain Tree", "Samanea saman", "Fabaceae", False),
    ("પળસ", "Flame of Forest", "Butea monosperma", "Fabaceae", True),
]

SMC_ZONES = [
    "Central Zone", "East Zone", "West Zone",
    "North Zone", "South Zone", "South-West Zone"
]

SURAT_AREAS = [
    "Athwa Lines", "Nanpura", "Majura Gate", "Varachha",
    "Katargam", "Udhna", "Adajan", "Piplod", "Vesu",
    "Ghod Dod Road", "Ring Road", "Dumas Road", "Hazira",
    "Jahangirpura", "Limbayat", "Rander", "Sachin",
    "Surat Railway Station Area", "Diamond Nagar", "VIP Road"
]

def seed_species():
    print("🌱 Seeding tree species...")
    count = 0
    for gu, en, bot, fam, native in SURAT_SPECIES:
        if not TreeSpecies.query.filter_by(common_name_english=en).first():
            sp = TreeSpecies(
                common_name_gujarati=gu,
                common_name_english=en,
                botanical_name=bot,
                family=fam,
                native=native
            )
            db.session.add(sp)
            count += 1
    db.session.commit()
    print(f"   ✅ Added {count} species")

def seed_admin():
    print("👑 Seeding admin user...")
    if not User.query.filter_by(email='admin@smc.gov.in').first():
        admin = User(
            username='admin',
            email='admin@smc.gov.in',
            password_hash=generate_password_hash('Admin@123'),
            full_name='SMC Administrator',
            role='admin',
            zone='All Zones',
            employee_id='SMC-ADMIN-001',
            phone='+91 261 2400000',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("   ✅ Admin: admin@smc.gov.in / Admin@123")
    else:
        print("   ℹ️  Admin already exists")

def seed_demo_users():
    print("👥 Seeding demo surveyors...")
    demo_users = [
        ("surveyor1", "Ramesh Patel", "surveyor1@smc.gov.in", "Central Zone", "Athwa"),
        ("surveyor2", "Priya Shah", "surveyor2@smc.gov.in", "East Zone", "Varachha"),
        ("surveyor3", "Amit Desai", "surveyor3@smc.gov.in", "West Zone", "Adajan"),
    ]
    for uname, fname, email, zone, ward in demo_users:
        if not User.query.filter_by(email=email).first():
            u = User(
                username=uname, email=email,
                password_hash=generate_password_hash('User@123'),
                full_name=fname, role='user',
                zone=zone, ward=ward,
                employee_id=f'SMC-{uname.upper()}-001',
                is_active=True
            )
            db.session.add(u)
    db.session.commit()
    print("   ✅ Demo surveyors: surveyor1/2/3@smc.gov.in / User@123")

def seed_sample_trees(count=50):
    print(f"🌳 Seeding {count} sample trees...")
    
    # ✅ Already trees hoy to skip
    if Tree.query.count() > 0:
        print(f"   ℹ️  Trees already exist, skipping...")
        return

    species_list = TreeSpecies.query.all()
    users = User.query.filter_by(role='user').all()
    
    if not species_list or not users:
        print("   ⚠️  Need species and users first!")
        return
    
    health_options = ['Excellent', 'Good', 'Good', 'Fair', 'Poor']
    location_types = ['Road Divider', 'Footpath', 'Park', 'Public Garden', 'School']
    BASE_LAT, BASE_LNG = 21.1702, 72.8311
    
    # ✅ Per-zone counter track karo
    zone_counters = {}
    
    for i in range(count):
        sp = random.choice(species_list)
        user = random.choice(users)
        
        lat = BASE_LAT + random.uniform(-0.15, 0.15)
        lng = BASE_LNG + random.uniform(-0.1, 0.1)
        
        height = round(random.uniform(3, 25), 1)
        dbh = round(random.uniform(10, 120), 1)
        girth = round(dbh * 3.14159, 1)
        agb = 0.0509 * (dbh ** 2) * height
        carbon = round(agb * 0.5, 2)
        
        zone_code = ''.join([c for c in user.zone if c.isupper()])[:2] or 'XX'
        
        # ✅ Counter increment karo per zone
        zone_counters[zone_code] = zone_counters.get(zone_code, 0) + 1
        tree_id = f"SMC-{zone_code}-{zone_counters[zone_code]:05d}"
        
        tree = Tree(
            tree_id=tree_id,
            latitude=lat, longitude=lng,
            altitude=round(random.uniform(15, 30), 1),
            gps_accuracy=round(random.uniform(2, 8), 1),
            zone=user.zone,
            ward=user.ward,
            area_name=random.choice(SURAT_AREAS),
            street_address=f"Near {random.choice(['Temple', 'School', 'Market', 'Hospital', 'Park'])}",
            location_type=random.choice(location_types),
            common_name_gujarati=sp.common_name_gujarati,
            common_name_english=sp.common_name_english,
            botanical_name=sp.botanical_name,
            family=sp.family,
            tree_height=height,
            trunk_girth=girth,
            canopy_spread_ns=round(random.uniform(3, 15), 1),
            canopy_spread_ew=round(random.uniform(3, 15), 1),
            dbh=dbh,
            health_condition=random.choice(health_options),
            structural_condition=random.choice(['Safe', 'Safe', 'Moderate Risk']),
            estimated_age=random.randint(5, 80),
            growth_stage=random.choice(['Young', 'Mature', 'Old']),
            soil_type=random.choice(['Sandy Loam', 'Clay', 'Loam', 'Sandy']),
            water_availability=random.choice(['Good', 'Moderate', 'Poor']),
            tree_guard=random.random() > 0.7,
            carbon_stock=carbon,
            oxygen_production=round(carbon * 2.67, 2),
            ecological_value=random.choice(['High', 'Medium', 'Low']),
            action_required=random.choice(['None', 'None', 'Pruning', 'Watering', 'Treatment']),
            priority=random.choice(['Low', 'Medium', 'Low']),
            surveyed_by=user.id,
            survey_date=datetime.utcnow(),
            status='active',
            is_verified=random.random() > 0.4
        )
        db.session.add(tree)
    
    db.session.commit()
    print(f"   ✅ Added {count} sample trees")
    
    

def ensure_database_exists(db_uri):
    """If target PostgreSQL database doesn't exist yet, attempt to create it via maintenance db."""
    if db_uri.startswith('postgresql'):
        from urllib.parse import urlparse
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        parsed = urlparse(db_uri)
        dbname = parsed.path.lstrip('/')
        if not dbname:
            return
            
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432
            )
            conn.close()
        except psycopg2.OperationalError as e:
            if 'does not exist' in str(e):
                print(f"⚙️ Target database '{dbname}' not found. Auto-creating on PostgreSQL server...")
                try:
                    maint_conn = psycopg2.connect(
                        dbname='postgres',
                        user=parsed.username,
                        password=parsed.password,
                        host=parsed.hostname,
                        port=parsed.port or 5432
                    )
                    maint_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cur = maint_conn.cursor()
                    cur.execute(f'CREATE DATABASE "{dbname}"')
                    cur.close()
                    maint_conn.close()
                    print(f"✅ Created PostgreSQL database: {dbname}")
                except Exception as create_err:
                    print(f"⚠️ Note: Run `createdb {dbname}` if auto-creation fails: {create_err}")


if __name__ == '__main__':
    with app.app_context():
        import re
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

        print("\n🚀 SMC Tree Census - Database Seeder")
        print("=" * 45)
        
        if db_uri.startswith('sqlite'):
            clean_path = db_uri.replace('sqlite:///', '')
            print(f"📦 Seeding SQLite Database: {clean_path}")
        else:
            masked = re.sub(r':([^@]+)@', ':****@', db_uri)
            print(f"🐘 Seeding PostgreSQL Database: {masked}")
            ensure_database_exists(db_uri)

        try:
            db.create_all()
            print("✅ Database tables verified/created\n")
        except Exception as e:
            print(f"\n❌ Database Connection Failed!")
            print(f"   Error: {e}\n")
            if 'postgresql' in db_uri:
                print("👉 PostgreSQL Troubleshooting:")
                print("   1. Check if PostgreSQL is running (service status)")
                print("   2. Verify port in .env (port 5432 vs 5433)")
                print("   3. Or switch to SQLite by setting in .env:")
                print("      DATABASE_URL=sqlite:///smc_tree_census.db\n")
            import sys
            sys.exit(1)
        
        seed_species()
        seed_admin()
        seed_demo_users()
        seed_sample_trees(50)
        
        print("\n✨ Seeding complete!")
        print("=" * 45)
        print("🔑 Login Credentials:")
        print("   Admin:     admin@smc.gov.in      / Admin@123")
        print("   Surveyor:  surveyor1@smc.gov.in  / User@123")
        print("\n🌐 Run: python app.py")
        print("   → http://localhost:5000\n")
