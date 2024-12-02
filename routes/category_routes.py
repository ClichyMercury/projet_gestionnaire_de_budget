from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.category import Category

category_bp = Blueprint('category', __name__)

# Create Category Route
@category_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_category = Category(
        name=data['name'],
        user_id=user_id,
        category_type=data['type'],
        description=data.get('description', ''),
        parent_id=data.get('parent_id')
    )
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify(message="Category created successfully!"), 201
    except:
        return jsonify(message="Category already exists."), 409

# List Categories Route
@category_bp.route('/categories', methods=['GET'])
@jwt_required()
def list_categories():
    user_id = get_jwt_identity()
    categories = Category.query.filter_by(user_id=user_id).all()
    categories_list = [
        {
            "id": c.id,
            "name": c.name,
            "type": c.category_type,
            "description": c.description,
            "parent_id": c.parent_id
        }
        for c in categories
    ]
    return jsonify(categories_list), 200

# Delete Category Route
@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    user_id = get_jwt_identity()
    category = Category.query.filter_by(id=category_id, user_id=user_id).first()
    if not category:
        return jsonify(message="Category not found"), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify(message="Category deleted successfully!"), 200
