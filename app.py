from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
from database import User, Meal, Order, Donation, init_db

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_business = data.get('is_business', False)

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    new_user = User(username=username, is_business=is_business)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['is_business'] = user.is_business
        return jsonify({'message': 'Login successful', 'user_id': user.id, 'is_business': user.is_business}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('is_business', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/@me', methods=['GET']) # Or /api/me, /api/current_user etc.
def get_current_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'user_id': user.id,
                'username': user.username,
                'is_business': user.is_business
            }), 200
    return jsonify({'message': 'Not logged in'}), 401

# Decorator for routes that require login
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Authentication is required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def business_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Authentication is required'}), 401
        if not session.get('is_business'):
            return jsonify({'message': 'Business account required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Meal Management Endpoints
@app.route('/meals', methods=['POST'])
@business_required
def create_meal():
    data = request.get_json()
    # Basic validation
    required_fields = ['name', 'original_price', 'discounted_price', 'quantity']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields for meal creation'}), 400

    new_meal = Meal(
        name=data['name'],
        description=data.get('description'),
        original_price=data['original_price'],
        discounted_price=data['discounted_price'],
        quantity=data['quantity'],
        pickup_time=data.get('pickup_time'),
        image_url=data.get('image_url'),
        business_id=session['user_id']
    )
    db.session.add(new_meal)
    db.session.commit()
    return jsonify({'message': 'Meal created successfully', 'meal_id': new_meal.id}), 201

@app.route('/meals', methods=['GET'])
def get_all_meals():
    meals = Meal.query.filter(Meal.quantity > 0).all() # Only show meals with available quantity
    output = []
    for meal in meals:
        meal_data = {
            'id': meal.id,
            'name': meal.name,
            'description': meal.description,
            'original_price': meal.original_price,
            'discounted_price': meal.discounted_price,
            'quantity': meal.quantity,
            'pickup_time': meal.pickup_time,
            'image_url': meal.image_url,
            'business_id': meal.business_id,
            'business_name': meal.business.username # Assuming User model has username for business
        }
        output.append(meal_data)
    return jsonify({'meals': output}), 200

@app.route('/meals/<int:meal_id>', methods=['GET'])
def get_meal_details(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    meal_data = {
        'id': meal.id,
        'name': meal.name,
        'description': meal.description,
        'original_price': meal.original_price,
        'discounted_price': meal.discounted_price,
        'quantity': meal.quantity,
        'pickup_time': meal.pickup_time,
        'image_url': meal.image_url,
        'business_id': meal.business_id,
        'business_name': meal.business.username
    }
    return jsonify(meal_data), 200

@app.route('/meals/<int:meal_id>', methods=['PUT'])
@business_required
def update_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.business_id != session['user_id']:
        return jsonify({'message': 'Forbidden: You can only update your own meals'}), 403

    data = request.get_json()
    meal.name = data.get('name', meal.name)
    meal.description = data.get('description', meal.description)
    meal.original_price = data.get('original_price', meal.original_price)
    meal.discounted_price = data.get('discounted_price', meal.discounted_price)
    meal.quantity = data.get('quantity', meal.quantity)
    meal.pickup_time = data.get('pickup_time', meal.pickup_time)
    meal.image_url = data.get('image_url', meal.image_url)

    db.session.commit()
    return jsonify({'message': 'Meal updated successfully'}), 200

@app.route('/meals/<int:meal_id>', methods=['DELETE'])
@business_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.business_id != session['user_id']:
        return jsonify({'message': 'Forbidden: You can only delete your own meals'}), 403

    # Consider implications: what happens to orders with this meal?
    # For now, simple deletion. Could mark as inactive instead.
    db.session.delete(meal)
    db.session.commit()
    return jsonify({'message': 'Meal deleted successfully'}), 200

@app.route('/business/meals', methods=['GET'])
@business_required
def get_business_meals():
    """Endpoint for a business to see all their listed meals (including those with 0 quantity)."""
    business_id = session['user_id']
    meals = Meal.query.filter_by(business_id=business_id).all()
    output = []
    for meal in meals:
        meal_data = {
            'id': meal.id,
            'name': meal.name,
            'description': meal.description,
            'original_price': meal.original_price,
            'discounted_price': meal.discounted_price,
            'quantity': meal.quantity,
            'pickup_time': meal.pickup_time,
            'image_url': meal.image_url
        }
        output.append(meal_data)
    return jsonify({'meals': output}), 200

# Order Management Endpoints
@app.route('/orders', methods=['POST'])
@login_required # Any logged-in user can create an order
def create_order():
    data = request.get_json()
    meal_id = data.get('meal_id')
    quantity = data.get('quantity', 1) # Default to 1 if not specified

    if not meal_id:
        return jsonify({'message': 'Meal ID is required'}), 400

    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({'message': 'Meal not found'}), 404

    if meal.quantity < quantity:
        return jsonify({'message': f'Not enough stock for {meal.name}. Available: {meal.quantity}'}), 400

    # Create order
    new_order = Order(
        user_id=session['user_id'],
        meal_id=meal_id,
        quantity=quantity,
        total_price=meal.discounted_price * quantity,
        status='Pending'
    )

    # Decrease meal quantity
    meal.quantity -= quantity

    db.session.add(new_order)
    db.session.commit()

    return jsonify({'message': 'Order created successfully', 'order_id': new_order.id}), 201

@app.route('/user/orders', methods=['GET'])
@login_required
def get_user_orders():
    """Fetch orders for the logged-in user."""
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    output = []
    for order in orders:
        order_data = {
            'order_id': order.id,
            'meal_name': order.meal.name, # Assumes meal relationship is loaded
            'quantity': order.quantity,
            'total_price': order.total_price,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': order.status
        }
        output.append(order_data)
    return jsonify({'orders': output}), 200

@app.route('/business/orders', methods=['GET'])
@business_required
def get_business_orders():
    """Fetch orders for meals listed by the logged-in business."""
    business_id = session['user_id']
    # Orders for meals where the meal's business_id matches the current user's id
    orders = Order.query.join(Meal).filter(Meal.business_id == business_id).order_by(Order.order_date.desc()).all()
    output = []
    for order in orders:
        order_data = {
            'order_id': order.id,
            'user_username': order.user.username, # Assumes user relationship is loaded
            'meal_name': order.meal.name,
            'quantity': order.quantity,
            'total_price': order.total_price,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': order.status
        }
        output.append(order_data)
    return jsonify({'orders': output}), 200

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
@business_required # Only businesses can update order status
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'message': 'New status is required'}), 400

    order = Order.query.get_or_404(order_id)

    # Check if the meal associated with the order belongs to this business
    if order.meal.business_id != session['user_id']:
        return jsonify({'message': 'Forbidden: You can only update status for orders of your meals'}), 403

    order.status = new_status
    db.session.commit()
    return jsonify({'message': f'Order {order_id} status updated to {new_status}'}), 200


# Donation Management Endpoints
@app.route('/donations', methods=['POST'])
@login_required
def create_donation():
    data = request.get_json()
    meal_id = data.get('meal_id') # Optional, for donating a specific meal
    organization_name = data.get('organization_name') # Optional, for general donation
    amount = data.get('amount') # Optional, for monetary donation not tied to a meal

    if not meal_id and not organization_name and not amount:
        return jsonify({'message': 'Donation details required (meal, organization, or amount)'}), 400

    user_id = session['user_id']

    if meal_id:
        meal = Meal.query.get(meal_id)
        if not meal:
            return jsonify({'message': 'Meal not found for donation'}), 404
        if meal.quantity < 1: # Assuming donating 1 unit of the meal
            return jsonify({'message': f'Meal {meal.name} is out of stock for donation'}), 400

        # Decrease meal quantity if a meal is donated
        meal.quantity -= 1
        # If no specific amount is given for a meal donation, it could be the meal's value or just the act of donating it
        # For simplicity, we're not assigning a monetary value here if a meal is donated directly,
        # but this could be expanded (e.g., use meal.discounted_price as amount).
        # The 'amount' field in Donation model is for general monetary donations.

    new_donation = Donation(
        user_id=user_id,
        meal_id=meal_id,
        organization_name=organization_name,
        amount=amount
    )
    db.session.add(new_donation)
    db.session.commit()

    return jsonify({'message': 'Donation successful', 'donation_id': new_donation.id}), 201

@app.route('/user/donations', methods=['GET'])
@login_required
def get_user_donations():
    """Fetch donations made by the logged-in user."""
    user_id = session['user_id']
    donations = Donation.query.filter_by(user_id=user_id).order_by(Donation.donation_date.desc()).all()
    output = []
    for donation in donations:
        donation_data = {
            'donation_id': donation.id,
            'meal_name': donation.meal.name if donation.meal else None,
            'organization_name': donation.organization_name,
            'amount': donation.amount,
            'donation_date': donation.donation_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        output.append(donation_data)
    return jsonify({'donations': output}), 200


if __name__ == '__main__':
    with app.app_context(): # Ensure app context for db operations
        init_db()
    app.run(debug=True)
