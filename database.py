from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_business = db.Column(db.Boolean, default=False) # True if user is a business/restaurant

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Meal Model
class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    pickup_time = db.Column(db.String(100), nullable=True) # Could be more structured (e.g., DateTime)
    image_url = db.Column(db.String(200), nullable=True)
    business_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    business = db.relationship('User', backref=db.backref('meals', lazy=True))

# Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String(50), default='Pending') # e.g., Pending, Completed, Cancelled

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    meal = db.relationship('Meal', backref=db.backref('orders', lazy=True))

# Donation Model
class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who made the donation
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=True) # Optional: if donation is for a specific meal
    # If meal_id is null, it can be a general donation to an organization
    organization_name = db.Column(db.String(100), nullable=True) # If donating to a specific org not tied to a meal
    amount = db.Column(db.Float, nullable=True) # Monetary value of donation if not a meal
    donation_date = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('donations', lazy=True))
    meal = db.relationship('Meal', backref=db.backref('donations', lazy=True))


def init_db():
    """Initializes the database and creates tables if they don't exist."""
    db.create_all()
    print("Database initialized and tables created.")

if __name__ == '__main__':
    # This allows running `python database.py` to create the database
    from app import app # Import app to provide context for db operations
    with app.app_context():
        init_db()
