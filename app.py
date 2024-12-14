from flask import Flask, send_from_directory, jsonify, render_template
import os
import re
import logging
from dotenv import load_dotenv
from extensions import db, jwt, bcrypt, migrate

load_dotenv()

def create_app():
   app = Flask(__name__)
   logging.basicConfig(level=logging.DEBUG)
   app.logger.setLevel(logging.DEBUG)
   
   if os.getenv('DATABASE_URL'):
       db_url = os.getenv('DATABASE_URL')
       if db_url.startswith('postgres://'):
           db_url = db_url.replace('postgres://', 'postgresql://')
       app.config['SQLALCHEMY_DATABASE_URI'] = db_url + "?sslmode=require"
   
   app.config['DEBUG'] = True
   app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
   app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

   db.init_app(app)
   jwt.init_app(app)
   bcrypt.init_app(app)
   migrate.init_app(app, db)

   with app.app_context():
       from flask_migrate import upgrade
       db.create_all()
       try:
           upgrade()
       except Exception as e:
           app.logger.error(f"Migration error: {str(e)}")

   from routes.web_routes import web_bp
   from routes.auth_routes import auth_bp
   from routes.transaction_routes import transaction_bp
   from routes.category_routes import category_bp
   from routes.report_routes import report

   app.register_blueprint(auth_bp, url_prefix='/auth')
   app.register_blueprint(transaction_bp, url_prefix='/api')
   app.register_blueprint(category_bp, url_prefix='/api')
   app.register_blueprint(report, url_prefix='/api')
   app.register_blueprint(web_bp)


   @app.route('/')
   def home():
       return render_template('base.html')

   @app.route('/favicon.ico')
   def favicon():
       return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

   @app.errorhandler(500)
   def handle_500(e):
       app.logger.error(f"500 Error: {str(e)}")
       return jsonify({
           'error': 'Internal server error',
           'message': str(e),
           'details': app.debug and str(e.__dict__) or None
       }), 500

   return app

app = create_app()

if __name__ == "__main__":
   app.run(debug=True)