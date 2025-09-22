from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, load_model
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Load ML model
try:
    model = load_model()
    print("Model loaded successfully.")
except Exception as e:
    print(f"Failed to load model: {e}")
    model = None

# Create tables
with app.app_context():
    db.create_all()

# Route to serve the pricing predictor HTML page
@app.route('/pricing')
def pricing_page():
    return render_template('pricing_predictor.html')

# Other routes...
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Form submitted.")
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Username: {username}")
        if not username or not password:
            print("Missing fields.")
            return render_template('register.html', message="Fill all fields")
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print("User exists.")
            return render_template('register.html', message="User already exists")
        # Hash password
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        # Create new user
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        print("User registered successfully.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                flash('Logged in successfully!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/pricing_predictor.html')
def pricing_predictor():
    return render_template('pricing_predictor.html')
    

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({'error': 'Model not loaded'}), 500
    data = request.get_json()
    try:
        distance = float(data.get('distance'))
        terrain = data.get('terrain')
        season = data.get('season')

        terrain_map = {'flat': 0, 'hilly': 1, 'mountainous': 2}
        season_map = {'dry': 0, 'rainy': 1, 'peak': 2}

        input_features = [
            distance,
            terrain_map.get(terrain, 0),
            season_map.get(season, 0)
        ]

        predicted_price = model.predict([input_features])[0]

        # Scenario analysis: vary distance ±10%
        high_distance = distance * 1.1
        low_distance = distance * 0.9

        scenario_high = model.predict([[high_distance, terrain_map.get(terrain, 0), season_map.get(season, 0)]])[0]
        scenario_low = model.predict([[low_distance, terrain_map.get(terrain, 0), season_map.get(season, 0)]])[0]

        return jsonify({
            'prediction': round(predicted_price, 2),
            'scenario_high': round(scenario_high, 2),
            'scenario_low': round(scenario_low, 2)
        })
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': 'Error during prediction'}), 500

if __name__ == '__main__':
    app.run(debug=True)