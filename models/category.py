from app import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_type = db.Column(db.String(10), nullable=False)  # Peut être "income" ou "expense"
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # Relation parent-enfant
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    description = db.Column(db.String(200))  # Description de la catégorie

    def __repr__(self):
        return f'<Category {self.name}>'
