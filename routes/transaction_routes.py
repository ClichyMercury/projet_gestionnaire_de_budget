from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.transaction import Transaction
from datetime import datetime

transaction_bp = Blueprint('transaction', __name__)

# Add Transaction Route
@transaction_bp.route('/transactions', methods=['POST'])
@jwt_required()
def add_transaction():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_transaction = Transaction(
        amount=data['amount'],
        description=data.get('description', ''),
        transaction_type=data['type'],
        category_id=data['category_id'],
        user_id=user_id,
        is_recurring=data.get('is_recurring', False),
        recurrence_interval=data.get('recurrence_interval'),
        status=data.get('status', 'completed'),
        payment_method=data.get('payment_method'),
        currency=data.get('currency', 'USD')
    )
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify(message="Transaction added successfully!"), 201

# Modify Transaction Route
@transaction_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def modify_transaction(transaction_id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    if not transaction:
        return jsonify(message="Transaction not found"), 404

    data = request.get_json()
    transaction.amount = data.get('amount', transaction.amount)
    transaction.description = data.get('description', transaction.description)
    transaction.transaction_type = data.get('type', transaction.transaction_type)
    transaction.category_id = data.get('category_id', transaction.category_id)
    transaction.is_recurring = data.get('is_recurring', transaction.is_recurring)
    transaction.recurrence_interval = data.get('recurrence_interval', transaction.recurrence_interval)
    transaction.status = data.get('status', transaction.status)
    transaction.payment_method = data.get('payment_method', transaction.payment_method)
    transaction.currency = data.get('currency', transaction.currency)
    db.session.commit()
    return jsonify(message="Transaction updated successfully!"), 200

# Delete Transaction Route
@transaction_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    if not transaction:
        return jsonify(message="Transaction not found"), 404

    db.session.delete(transaction)
    db.session.commit()
    return jsonify(message="Transaction deleted successfully!"), 200

# List Transactions Route
@transaction_bp.route('/transactions', methods=['GET'])
@jwt_required()
def list_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    transactions_list = [
        {
            "id": t.id,
            "amount": t.amount,
            "type": t.transaction_type,
            "category_id": t.category_id,
            "description": t.description,
            "date": t.date.strftime("%Y-%m-%d %H:%M:%S"),
            "is_recurring": t.is_recurring,
            "recurrence_interval": t.recurrence_interval,
            "status": t.status,
            "payment_method": t.payment_method,
            "currency": t.currency
        }
        for t in transactions
    ]
    return jsonify(transactions_list), 200