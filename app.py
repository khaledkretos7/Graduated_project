from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db, User, Post, Message, PublicService, Advertisement
from socket_instance import socketio
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.admin import admin_bp
from routes.messages import messages_bp
from routes.public_services import public_services_bp
from routes.advertisements import advertisements_bp
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Configure CORS to allow requests from the frontend with credentials
CORS(app, 
     resources={r"/api/*": {
         "origins": "http://localhost:5173", 
         "supports_credentials": True,
         "allow_headers": ["Content-Type", "Authorization"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
     }},
     send_wildcard=False)


# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['BASE_URL'] = 'http://localhost:5000'

# Initialize extensions
jwt = JWTManager(app)
db.init_app(app)

# Initialize SocketIO with our Flask app
socketio.init_app(app, cors_allowed_origins="http://localhost:5173")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(posts_bp, url_prefix='/api/posts')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(public_services_bp, url_prefix='/api/public-services')
app.register_blueprint(advertisements_bp, url_prefix='/api/advertisements')

# Create a CLI command to initialize the database
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    print('Database tables created.')

# Create tables within application context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return jsonify({"message": "Welcome to Neighborhood Forum API"})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('new_post')
def handle_new_post(data):
    # Broadcast the new post to all connected clients
    socketio.emit('post_update', data)

@socketio.on('new_message')
def handle_new_message(data):
    # Broadcast the new message to all connected clients
    socketio.emit('message_update', data)

if __name__ == '__main__':
    socketio.run(app, debug=True)
