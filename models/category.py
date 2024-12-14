from app import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_type = db.Column(db.String(10), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    description = db.Column(db.String(200))

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_category_per_user'),
    )

    def __repr__(self):
        return f'<Category {self.name}>'
