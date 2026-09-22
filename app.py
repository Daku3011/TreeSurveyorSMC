from flask import Flask, redirect, url_for, render_template
from extensions import db, login_manager, migrate
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smc-tree-census-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/smc_tree_census'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
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
            print("✅ Default admin created!")
    app.run(debug=True, host='0.0.0.0', port=5000)