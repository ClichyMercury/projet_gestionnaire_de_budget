from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
import csv
from reportlab.pdfgen import canvas
from models import Transaction  # Supposons que Transaction soit ton modèle SQLAlchemy
from app import db

# Utiliser un backend sans GUI pour Matplotlib
plt.switch_backend('Agg')

report = Blueprint('report', __name__)

@report.route('/report/monthly', methods=['GET'])
@jwt_required()
def generate_monthly_report():
    user_id = get_jwt_identity()
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Récupérer les transactions du mois en cours pour l'utilisateur
    transactions = Transaction.query.filter_by(user_id=user_id).filter(
        db.extract('month', Transaction.date) == current_month,
        db.extract('year', Transaction.date) == current_year
    ).all()

    # Calculer les revenus et dépenses par catégorie
    categories = {}
    for transaction in transactions:
        if transaction.category.name not in categories:
            categories[transaction.category.name] = 0
        categories[transaction.category.name] += transaction.amount if transaction.transaction_type == 'income' else -transaction.amount

    # Générer un graphique
    fig, ax = plt.subplots()

    # Convertir les clés des catégories en chaînes de caractères
    categories_keys = [str(key) for key in categories.keys()]
    categories_values = list(categories.values())

    ax.bar(categories_keys, categories_values)
    ax.set_title('Revenus et Dépenses par Catégorie')
    ax.set_xlabel('Catégories')
    ax.set_ylabel('Montant (€)')
    plt.xticks(rotation=45)

    # Sauvegarder le graphique en mémoire pour l'inclure dans la réponse
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{encoded_img}"

    # Retourner les données du graphique et un résumé
    total_income = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'income')
    total_expense = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'expense')
    balance = total_income - total_expense

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "chart": img_data
    })

@report.route('/report/annual', methods=['GET'])
@jwt_required()
def generate_annual_report():
    user_id = get_jwt_identity()
    current_year = datetime.now().year

    # Récupérer les transactions de l'année en cours pour l'utilisateur
    transactions = Transaction.query.filter_by(user_id=user_id).filter(
        db.extract('year', Transaction.date) == current_year
    ).all()

    # Calculer les revenus et dépenses par catégorie
    categories = {}
    for transaction in transactions:
        if transaction.category.name not in categories:
            categories[transaction.category.name] = 0
        categories[transaction.category.name] += transaction.amount if transaction.transaction_type == 'income' else -transaction.amount

    # Générer le graphique
    fig, ax = plt.subplots()

    # Convertir les clés des catégories en chaînes de caractères
    categories_keys = [str(key) for key in categories.keys()]
    categories_values = list(categories.values())

    ax.bar(categories_keys, categories_values)
    ax.set_title('Revenus et Dépenses Annuels par Catégorie')
    ax.set_xlabel('Catégories')
    ax.set_ylabel('Montant (€)')
    plt.xticks(rotation=45)

    # Sauvegarder le graphique en mémoire pour l'inclure dans la réponse
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{encoded_img}"

    # Retourner les données du graphique et un résumé
    total_income = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'income')
    total_expense = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'expense')
    balance = total_income - total_expense

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "chart": img_data
    })

@report.route('/report/custom', methods=['GET'])
@jwt_required()
def generate_custom_report():
    user_id = get_jwt_identity()
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Les dates doivent être au format YYYY-MM-DD"}), 400

    # Récupérer les transactions pour la plage de dates spécifiée
    transactions = Transaction.query.filter_by(user_id=user_id).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    # Calculer les revenus et dépenses par catégorie
    categories = {}
    for transaction in transactions:
        if transaction.category.name not in categories:
            categories[transaction.category.name] = 0
        categories[transaction.category.name] += transaction.amount if transaction.transaction_type == 'income' else -transaction.amount

    # Générer le graphique
    fig, ax = plt.subplots()

    # Convertir les clés des catégories en chaînes de caractères
    categories_keys = [str(key) for key in categories.keys()]
    categories_values = list(categories.values())

    ax.bar(categories_keys, categories_values)
    ax.set_title(f'Revenus et Dépenses du {start_date_str} au {end_date_str}')
    ax.set_xlabel('Catégories')
    ax.set_ylabel('Montant (€)')
    plt.xticks(rotation=45)

    # Sauvegarder le graphique en mémoire pour l'inclure dans la réponse
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{encoded_img}"

    # Retourner les données du graphique et un résumé
    total_income = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'income')
    total_expense = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'expense')
    balance = total_income - total_expense

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "chart": img_data
    })

@report.route('/report/export/csv', methods=['GET'])
@jwt_required()
def export_transactions_csv():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # Créer un fichier CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Montant', 'Catégorie', 'Description'])

    for transaction in transactions:
        writer.writerow([
            transaction.date.strftime('%Y-%m-%d'),
            transaction.transaction_type,
            transaction.amount,
            transaction.category.name,
            transaction.description
        ])

    # Retourner le fichier CSV
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=transactions.csv"})

@report.route('/report/export/pdf', methods=['GET'])
@jwt_required()
def export_transactions_pdf():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # Créer un PDF en mémoire
    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer)
    pdf.setTitle("Rapport des Transactions")

    pdf.drawString(100, 800, "Rapport des Transactions Financières")
    y_position = 780

    for transaction in transactions:
        pdf.drawString(100, y_position, f"Date: {transaction.date.strftime('%Y-%m-%d')} | Type: {transaction.transaction_type} | Montant: {transaction.amount} | Catégorie: {transaction.category.name} | Description: {transaction.description}")
        y_position -= 20
        if y_position < 50:
            pdf.showPage()
            y_position = 800

    pdf.save()
    pdf_buffer.seek(0)

    # Retourner le fichier PDF
    return Response(pdf_buffer, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=transactions.pdf"})
