"""
WSGI Entry Point for Production Deployment (Render, Heroku, Docker)
Usage: gunicorn wsgi:app
"""
import os
from app import create_app
from extensions import db

app = create_app()

# Auto-initialize database tables and default admin upon deployment
with app.app_context():
    try:
        db.create_all()
        from models.user import User
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                username='admin',
                email='admin@smc.gov.in',
                password_hash=generate_password_hash('Admin@123'),
                full_name='SMC Administrator',
                role='admin',
                zone='All Zones',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Production admin account initialized.")
    except Exception as e:
        print(f"⚠️ Note during startup DB check: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
