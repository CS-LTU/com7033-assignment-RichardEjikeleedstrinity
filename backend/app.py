from flask import Flask, jsonify, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv
from api.help_utils.mongodb import mongo
from api.database.database import init_app
load_dotenv()



def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # MongoDB Configuration
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/stroke_prediction')
    
    # Validate and set MongoDB URI
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is not set")
    
    app.config['MONGO_URI'] = mongodb_uri
    
    # Print connection info (for debugging, remove in production)
    print(f"Attempting to connect to MongoDB...")
    print(f"URI: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri}")
    
    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True
        }
    })
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize MongoDB with error handling
    try:
        mongo.init_app(app, uri=app.config['MONGO_URI'])
        print("MongoDB extension initialized")
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")
        raise
        # Initialize SQLite Database
    

    try:
        init_app(app)
        print("SqliteDB extension initialized")
    except Exception as e:
        print(f"Error initializing SqliteDB: {e}")
        raise
    # Test MongoDB connection
    with app.app_context():
        try:
            # Test connection
            print("Testing MongoDB connection...")
            mongo.db.command('ping')
            print("✅ MongoDB connection successful!")
            
            # Initialize database with default data
            from api.help_utils.mongodb_service import MongoDBService
            MongoDBService.init_db(app)
        except ConnectionFailure as e:
            print(f"❌ MongoDB Connection Failure: {e}")
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB Server Selection Timeout: {e}")
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
    
    # Import blueprints AFTER mongo is initialized
    from api.auth.routes import auth_bp

    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
       
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/health')
    def health_check():
        try:
            # Test MongoDB connection
            mongo.db.command('ping')
            collections = mongo.db.list_collection_names()
            return jsonify({
                'status': 'healthy',
                'message': 'API and MongoDB are running',
                'mongodb': 'connected',
                'database': mongo.db.name,
                'collections': collections
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'message': 'MongoDB connection failed',
                'error': str(e),
                'mongodb_uri_used': app.config['MONGO_URI'].split('@')[-1] if '@' in app.config['MONGO_URI'] else app.config['MONGO_URI']
            }), 500
    
    @app.route('/api/test-mongo')
    def test_mongo():
        """Test endpoint to check MongoDB connection details"""
        try:
            client = mongo.cx
            db = mongo.db
            info = {
                'client_connected': client is not None,
                'db_connected': db is not None,
                'database_name': db.name if db else None,
                'collections': db.list_collection_names() if db else [],
                'server_info': str(client.server_info()) if client else None
            }
            return jsonify(info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/init-db', methods=['POST'])
    def init_database():
        """Initialize database with sample data (for testing)"""
        try:
            from api.help_utils.mongodb_service import MongoDBService
            MongoDBService.init_db(app)
            return jsonify({'message': 'Database initialized successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=3000)