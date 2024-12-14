import base64
import csv
import io
from datetime import datetime
from functools import wraps

import matplotlib.pyplot as plt
from flask import (Blueprint, Response, flash, jsonify, redirect, render_template,
                  request, session, url_for)
from reportlab.pdfgen import canvas

from extensions import db
from models.category import Category
from models.transaction import Transaction
from models.user import User

web_bp = Blueprint('web', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is None:
            flash('Veuillez vous connecter pour accéder à cette page.', 'error')
            return redirect(url_for('web.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@web_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).limit(5).all()
    categories = Category.query.filter_by(user_id=user_id).all()
    total_expenses = sum(t.amount for t in Transaction.query.filter(
        Transaction.amount < 0,
        Transaction.user_id == user_id
    ).all())
    total_income = sum(t.amount for t in Transaction.query.filter(
        Transaction.amount > 0,
        Transaction.user_id == user_id
    ).all())
    return render_template('dashboard.html', 
                         transactions=transactions,
                         categories=categories,
                         total_expenses=total_expenses,
                         total_income=total_income)

@web_bp.route('/transactions', methods=['GET'], endpoint='transactions_list')  # changé l'endpoint
@login_required
def transactions():
    user_id = session.get('user_id')
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('transactions/index.html', 
                         transactions=transactions,
                         categories=categories)

@web_bp.route('/transactions/new', methods=['GET', 'POST'], endpoint='new_transaction')  # changé l'endpoint
@login_required
def new_transaction():
    user_id = session.get('user_id')
    if request.method == 'POST':
        category = Category.query.get(request.form.get('category_id'))
        transaction = Transaction(
            description=request.form.get('description'),
            amount=float(request.form.get('amount')),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            category=category,
            user_id=user_id,  # Ajout du user_id
            transaction_type='expense' if float(request.form.get('amount')) < 0 else 'income',
            status='completed',
            currency='EUR'  # ou la devise par défaut de votre choix
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction créée avec succès!', 'success')
        return redirect(url_for('web.transactions'))
    
    categories = Category.query.filter_by(user_id=user_id).all()  # Filtrer par user_id
    return render_template('transactions/new.html', categories=categories)

@web_bp.route('/transactions')
@login_required
def transactions():
    user_id = session.get('user_id')
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('transactions/index.html', 
                         transactions=transactions,
                         categories=categories)


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Connexion réussie!', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('Identifiants invalides.', 'error')
    
    return render_template('auth/login.html')


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Nom d\'utilisateur déjà utilisé.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email déjà utilisé.', 'error')
            return render_template('auth/register.html')

        # Gérer l'upload de la photo de profil
        profile_picture = request.files.get('profile_picture')
        profile_picture_base64 = None
        if profile_picture:
            profile_picture_base64 = base64.b64encode(profile_picture.read()).decode('utf-8')

        # Créer le nouvel utilisateur
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            password=request.form.get('password'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            profile_picture=profile_picture_base64
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('web.login'))

    return render_template('auth/register.html')


@web_bp.route('/categories', methods=['GET'])
@login_required
def categories():
    user_id = session.get('user_id')
    if not user_id:
        flash('Veuillez vous connecter.', 'error')
        return redirect(url_for('web.login'))
        
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('categories/index.html', categories=categories)
@web_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    user_id = session.get('user_id')
    if not user_id:
        flash('Veuillez vous connecter.', 'error')
        return redirect(url_for('web.login'))

    # Récupérer toutes les catégories existantes pour cet utilisateur
    parent_categories = Category.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        parent_id = request.form.get('parent_id')
        # Convertir en None si vide, sinon en integer
        parent_id = int(parent_id) if parent_id else None
        
        try:
            new_category = Category(
                name=request.form.get('name'),
                user_id=user_id,
                category_type=request.form.get('type'),
                description=request.form.get('description'),
                parent_id=parent_id
            )
            
            db.session.add(new_category)
            db.session.commit()
            flash('Catégorie créée avec succès!', 'success')
            return redirect(url_for('web.categories'))
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de la catégorie: {str(e)}")
            flash('Erreur lors de la création de la catégorie.', 'error')
    
    return render_template('categories/new.html', parent_categories=parent_categories)

@web_bp.route('/categories/delete/<int:category_id>', methods=['POST'] )
@login_required
def delete_category(category_id):
    user_id = session.get('user_id')
    category = Category.query.filter_by(id=category_id, user_id=user_id).first()
    
    if not category:
        flash('Catégorie non trouvée.', 'error')
        return redirect(url_for('web.categories'))

    # Vérifier si des transactions sont liées à cette catégorie
    transactions = Transaction.query.filter_by(category_id=category_id).first()
    if transactions:
        flash('Impossible de supprimer cette catégorie car elle contient des transactions.', 'error')
        return redirect(url_for('web.categories'))

    try:
        db.session.delete(category)
        db.session.commit()
        flash('Catégorie supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la catégorie: {str(e)}', 'error')
    
    return redirect(url_for('web.categories'))


@web_bp.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('web.login'))

@web_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('web.dashboard'))
    return redirect(url_for('web.login'))


@web_bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'], endpoint='edit_transaction')  # changé l'endpoint
@login_required
def edit_transaction(transaction_id):
    user_id = session.get('user_id')
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    
    if not transaction:
        flash('Transaction non trouvée.', 'error')
        return redirect(url_for('web.transactions'))
    
    if request.method == 'POST':
        category = Category.query.get(request.form.get('category_id'))
        transaction.description = request.form.get('description')
        transaction.amount = float(request.form.get('amount'))
        transaction.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        transaction.category = category
        transaction.transaction_type = 'expense' if float(request.form.get('amount')) < 0 else 'income'
        
        db.session.commit()
        flash('Transaction modifiée avec succès!', 'success')
        return redirect(url_for('web.transactions'))
    
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('transactions/edit.html', 
                         transaction=transaction,
                         categories=categories)

@web_bp.route('/transactions/delete/<int:transaction_id>', methods=['POST'], endpoint='delete_transaction')  # changé l'endpoint
@login_required
def delete_transaction(transaction_id):
    user_id = session.get('user_id')
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    
    if not transaction:
        flash('Transaction non trouvée.', 'error')
        return redirect(url_for('web.transactions'))
    
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction supprimée avec succès!', 'success')
    return redirect(url_for('web.transactions'))


@web_bp.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        flash('Utilisateur non trouvé.', 'error')
        return redirect(url_for('web.dashboard'))
    
    return render_template('profile/index.html', user=user)

@web_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('Utilisateur non trouvé.', 'error')
        return redirect(url_for('web.dashboard'))
    
    try:
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        
        # Gestion de la photo de profil
        profile_picture = request.files.get('profile_picture')
        if profile_picture:
            # Convertir l'image en base64
            profile_picture_base64 = base64.b64encode(profile_picture.read()).decode('utf-8')
            user.profile_picture = profile_picture_base64
        
        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour du profil: {str(e)}', 'error')
    
    return redirect(url_for('web.profile'))

@web_bp.route('/report/monthly', methods=['GET'])
@login_required
def generate_monthly_report():
    user_id = session.get('user_id')
    current_month = datetime.now().month
    current_year = datetime.now().year

    try:
        # Récupérer les transactions du mois en cours pour l'utilisateur
        transactions = Transaction.query.filter_by(user_id=user_id).filter(
            db.extract('month', Transaction.date) == current_month,
            db.extract('year', Transaction.date) == current_year
        ).all()

        # Déterminer la devise la plus utilisée pour ce mois
        currency_counts = {}
        for t in transactions:
            currency_counts[t.currency] = currency_counts.get(t.currency, 0) + 1
        most_used_currency = max(currency_counts.items(), key=lambda x: x[1])[0] if currency_counts else 'EUR'

        # Calculer les revenus et dépenses par catégorie
        categories = {}
        for transaction in transactions:
            if transaction.category.name not in categories:
                categories[transaction.category.name] = 0
            # Convertir le montant si nécessaire (tu devras implémenter la conversion)
            amount = transaction.amount  # Ajouter la conversion ici si nécessaire
            categories[transaction.category.name] += amount if transaction.transaction_type == 'income' else -amount

        # Générer le graphique
        plt.figure(figsize=(10, 6))
        plt.clf()

        categories_keys = [str(key) for key in categories.keys()]
        categories_values = list(categories.values())

        plt.bar(categories_keys, categories_values)
        plt.title('Revenus et Dépenses par Catégorie')
        plt.xlabel('Catégories')
        plt.ylabel(f'Montant ({most_used_currency})')
        plt.xticks(rotation=45)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
        img_data = f"data:image/png;base64,{encoded_img}"
        plt.close()

        total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        balance = total_income - total_expense

        return jsonify({
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "chart": img_data,
            "categories": categories,
            "currency": most_used_currency
        })

    except Exception as e:
        print(f"Erreur lors de la génération du rapport mensuel: {str(e)}")
        return jsonify({"error": "Erreur lors de la génération du rapport"}), 500

@web_bp.route('/report/annual', methods=['GET'])
@login_required
def generate_annual_report():
    user_id = session.get('user_id')
    current_year = datetime.now().year

    try:
        transactions = Transaction.query.filter_by(user_id=user_id).filter(
            db.extract('year', Transaction.date) == current_year
        ).all()

        categories = {}
        for transaction in transactions:
            if transaction.category.name not in categories:
                categories[transaction.category.name] = 0
            categories[transaction.category.name] += transaction.amount if transaction.transaction_type == 'income' else -transaction.amount

        plt.figure(figsize=(10, 6))
        plt.clf()

        categories_keys = [str(key) for key in categories.keys()]
        categories_values = list(categories.values())

        plt.bar(categories_keys, categories_values)
        plt.title('Revenus et Dépenses Annuels par Catégorie')
        plt.xlabel('Catégories')
        plt.ylabel('Montant (€)')
        plt.xticks(rotation=45)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
        img_data = f"data:image/png;base64,{encoded_img}"
        plt.close()

        total_income = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'income')
        total_expense = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'expense')
        balance = total_income - total_expense

        return jsonify({
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "chart": img_data,
            "categories": categories
        })

    except Exception as e:
        print(f"Erreur lors de la génération du rapport annuel: {str(e)}")
        return jsonify({"error": "Erreur lors de la génération du rapport"}), 500

@web_bp.route('/report/custom', methods=['GET'])
@login_required
def generate_custom_report():
    user_id = session.get('user_id')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Les dates doivent être au format YYYY-MM-DD"}), 400

    try:
        transactions = Transaction.query.filter_by(user_id=user_id).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()

        categories = {}
        for transaction in transactions:
            if transaction.category.name not in categories:
                categories[transaction.category.name] = 0
            categories[transaction.category.name] += transaction.amount if transaction.transaction_type == 'income' else -transaction.amount

        plt.figure(figsize=(10, 6))
        plt.clf()

        categories_keys = [str(key) for key in categories.keys()]
        categories_values = list(categories.values())

        plt.bar(categories_keys, categories_values)
        plt.title(f'Revenus et Dépenses du {start_date_str} au {end_date_str}')
        plt.xlabel('Catégories')
        plt.ylabel('Montant (€)')
        plt.xticks(rotation=45)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
        img_data = f"data:image/png;base64,{encoded_img}"
        plt.close()

        total_income = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'income')
        total_expense = sum(transaction.amount for transaction in transactions if transaction.transaction_type == 'expense')
        balance = total_income - total_expense

        return jsonify({
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "chart": img_data,
            "categories": categories
        })

    except Exception as e:
        print(f"Erreur lors de la génération du rapport personnalisé: {str(e)}")
        return jsonify({"error": "Erreur lors de la génération du rapport"}), 500

@web_bp.route('/reports')
@login_required
def reports():
    try:
        return render_template('report/index.html')
    except Exception as e:
        print(f"Erreur lors du chargement de la page rapports: {str(e)}")
        flash('Une erreur est survenue lors du chargement des rapports.', 'error')
        return redirect(url_for('web.dashboard'))
    

@web_bp.route('/report/export/csv', methods=['GET'])
@login_required
def export_transactions_csv():
    user_id = session.get('user_id')
    
    try:
        # Récupérer les transactions triées par date
        transactions = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.date.desc())\
            .all()

        # Créer un fichier CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')  # Utiliser ; pour meilleure compatibilité Excel français
        
        # Écrire l'en-tête
        writer.writerow([
            'Date',
            'Type',
            'Description',
            'Catégorie',
            'Montant',
            'Devise',
            'Méthode de paiement',
            'Récurrent',
            'Intervalle de récurrence'
        ])

        # Écrire les transactions
        for transaction in transactions:
            writer.writerow([
                transaction.date.strftime('%d/%m/%Y'),
                'Revenu' if transaction.transaction_type == 'income' else 'Dépense',
                transaction.description,
                transaction.category.name if transaction.category else 'Non catégorisé',
                "{:.2f}".format(abs(transaction.amount)),
                transaction.currency,
                transaction.payment_method,
                'Oui' if transaction.is_recurring else 'Non',
                transaction.recurrence_interval if transaction.is_recurring else 'N/A'
            ])

        # Préparer la réponse
        output.seek(0)
        return Response(
            output,
            mimetype='text/csv',
            headers={
                "Content-Disposition": "attachment;filename=transactions.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        print(f"Erreur lors de l'export CSV: {str(e)}")
        flash('Erreur lors de l\'export des transactions en CSV.', 'error')
        return redirect(url_for('web.reports'))

@web_bp.route('/report/export/pdf', methods=['GET'])
@login_required
def export_transactions_pdf():
    user_id = session.get('user_id')
    
    try:
        # Récupérer les transactions triées par date
        transactions = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.date.desc())\
            .all()

        # Créer un PDF en mémoire
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.setTitle("Rapport des Transactions")

        # Configurer la police et les styles
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 800, "Rapport des Transactions Financières")
        pdf.setFont("Helvetica", 10)
        
        # Ajouter la date du rapport
        pdf.drawString(50, 780, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        
        # Dessiner les en-têtes du tableau
        y_position = 750
        headers = ['Date', 'Type', 'Description', 'Catégorie', 'Montant', 'Devise']
        x_positions = [50, 120, 180, 300, 420, 480]
        
        pdf.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            pdf.drawString(x_positions[i], y_position, header)
        
        # Dessiner les lignes de transactions
        pdf.setFont("Helvetica", 10)
        y_position -= 20
        
        # Calculer les totaux par devise
        totals = {}
        
        for transaction in transactions:
            # Vérifier s'il reste assez d'espace sur la page
            if y_position < 50:
                pdf.showPage()
                y_position = 750
                
                # Redessiner les en-têtes sur la nouvelle page
                pdf.setFont("Helvetica-Bold", 10)
                for i, header in enumerate(headers):
                    pdf.drawString(x_positions[i], y_position, header)
                pdf.setFont("Helvetica", 10)
                y_position -= 20
            
            # Ajouter au total
            currency = transaction.currency
            if currency not in totals:
                totals[currency] = {'income': 0, 'expense': 0}
            
            if transaction.transaction_type == 'income':
                totals[currency]['income'] += transaction.amount
            else:
                totals[currency]['expense'] += abs(transaction.amount)
            
            # Écrire la ligne de transaction
            pdf.drawString(x_positions[0], y_position, transaction.date.strftime('%d/%m/%Y'))
            pdf.drawString(x_positions[1], y_position, 
                         'Revenu' if transaction.transaction_type == 'income' else 'Dépense')
            
            # Tronquer la description si elle est trop longue
            description = transaction.description
            if len(description) > 20:
                description = description[:17] + "..."
            pdf.drawString(x_positions[2], y_position, description)
            
            # Catégorie
            category = transaction.category.name if transaction.category else 'Non catégorisé'
            pdf.drawString(x_positions[3], y_position, category)
            
            # Montant
            amount = "{:,.2f}".format(abs(transaction.amount)).replace(',', ' ')
            pdf.drawString(x_positions[4], y_position, amount)
            
            # Devise
            pdf.drawString(x_positions[5], y_position, transaction.currency)
            
            y_position -= 20
        
        # Ajouter un résumé à la fin
        pdf.showPage()
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, 800, "Résumé par devise")
        
        y_position = 770
        pdf.setFont("Helvetica", 12)
        
        for currency, amounts in totals.items():
            pdf.drawString(50, y_position, f"Devise : {currency}")
            pdf.drawString(70, y_position - 20, f"Total revenus : {amounts['income']:,.2f} {currency}")
            pdf.drawString(70, y_position - 40, f"Total dépenses : {amounts['expense']:,.2f} {currency}")
            pdf.drawString(70, y_position - 60, 
                         f"Balance : {amounts['income'] - amounts['expense']:,.2f} {currency}")
            y_position -= 100

        # Sauvegarder le PDF
        pdf.save()
        buffer.seek(0)
        
        return Response(
            buffer,
            mimetype='application/pdf',
            headers={
                "Content-Disposition": "attachment;filename=transactions.pdf",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        print(f"Erreur lors de l'export PDF: {str(e)}")
        flash('Erreur lors de l\'export des transactions en PDF.', 'error')
        return redirect(url_for('web.reports'))

