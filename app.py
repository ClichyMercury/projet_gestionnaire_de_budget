from flask import Flask, send_from_directory
import os
from dotenv import load_dotenv
from extensions import db, jwt, bcrypt, migrate

# Charger les variables d'environnement
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configurer l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialiser les extensions avec l'app
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.transaction_routes import transaction_bp
    from routes.category_routes import category_bp
    from routes.report_routes import report

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(category_bp, url_prefix='/api')
    app.register_blueprint(report, url_prefix='/api')

    @app.route('/')
    def home():
        return "Bienvenue sur le Gestionnaire de Budget !"

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
