from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from app import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

# Register Route
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify(message="Username already exists."), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify(message="Email already exists."), 409
    
    # Extract data from request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    profile_picture = data.get('profile_picture')  # Should be a base64 string
    
    # Create new user instance
    new_user = User(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        profile_picture=profile_picture
    )
    
    # Add new user to database
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': "User registered successfully!",
        'username': new_user.username,
        'email': new_user.email,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name
    }), 201

# Login Route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(
            access_token=access_token,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_picture=user.profile_picture
        ), 200

    return jsonify(message="Invalid credentials"), 401

# Delete Account
@auth_bp.route('/delete_account/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_account(user_id):
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message="User account deleted successfully!"), 200

    return jsonify(message="User not found."), 404
