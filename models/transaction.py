from app import db
from datetime import datetime

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    transaction_type = db.Column(db.String(10), nullable=False)  # "income" ou "expense"
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)  # Champ pour indiquer si la transaction est récurrente
    recurrence_interval = db.Column(db.String(20))  # "daily", "weekly", "monthly", etc.
    status = db.Column(db.String(20), default="completed")  # Peut être "pending", "completed", "failed"
    payment_method = db.Column(db.String(30))  # "cash", "credit card", "bank transfer", etc.
    currency = db.Column(db.String(10), default="USD")  # Devise de la transaction

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    category = db.relationship('Category', backref=db.backref('transactions', lazy=True))

        # Dans Transaction model
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'date'),
    )


    def __repr__(self):
        return f'<Transaction {self.description} - {self.amount}>'
