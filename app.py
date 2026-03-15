import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from database_models import db, User, FarmHistory
from models.rl_model import IrrigationQLearning

app = Flask(__name__)
rl_engine = IrrigationQLearning(load_path='models/q_table.pkl')
app.config['SECRET_KEY'] = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'irrigation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables if they don't exist
with app.app_context():
    os.makedirs('database', exist_ok=True)
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        farmer_name = request.form.get('farmer_name')
        email = request.form.get('email')
        password = request.form.get('password')
        farm_location = request.form.get('farm_location')
        farm_size = request.form.get('farm_size')
        preferred_crops = request.form.get('preferred_crops')
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            farmer_name=farmer_name,
            email=email,
            password_hash=hashed_password,
            farm_location=farm_location,
            farm_size=float(farm_size) if farm_size else None,
            preferred_crops=preferred_crops
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    latest_history = FarmHistory.query.filter_by(user_id=current_user.id).order_by(FarmHistory.timestamp.desc()).first()
    history_records = FarmHistory.query.filter_by(user_id=current_user.id).order_by(FarmHistory.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html', latest_history=latest_history, history_records=history_records)

@app.route('/crop_selection')
@login_required
def crop_selection():
    return render_template('crop_selection.html')

@app.route('/irrigation_input', methods=['GET', 'POST'])
@login_required
def irrigation_input():
    if request.method == 'POST':
        crop_type = request.form.get('crop_type')
        soil_moisture = float(request.form.get('soil_moisture'))
        temperature = float(request.form.get('temperature'))
        humidity = float(request.form.get('humidity'))
        rainfall_level = float(request.form.get('rainfall_level'))
        weather_type = request.form.get('weather_type')
        
        # Get AI Decision
        rec = rl_engine.get_recommendation(crop_type, soil_moisture, temperature, rainfall_level)
        
        # Update RL Model Q-Table slightly and save
        # In a real system, reward would be gathered later based on crop yield/survival.
        # Here we simulate an immediate learning step.
        rl_engine.update_q_table(rec['state_tuple'], rec['action_index'], rec['simulated_reward'], rec['state_tuple'])
        rl_engine.save_model('models/q_table.pkl')
        
        # Save to DB
        new_history = FarmHistory(
            user_id=current_user.id,
            crop_type=crop_type,
            soil_moisture=soil_moisture,
            temperature=temperature,
            humidity=humidity,
            rainfall_level=rainfall_level,
            weather_type=weather_type,
            irrigation_decision=rec['decision'],
            water_amount=rec['water_amount'],
            reward=rec['simulated_reward']
        )
        db.session.add(new_history)
        db.session.commit()
        
        # Render template with recommendation to show Modal
        return render_template('irrigation_input.html', recommendation=rec)
        
    return render_template('irrigation_input.html')

@app.route('/analytics')
@login_required
def analytics():
    records = FarmHistory.query.filter_by(user_id=current_user.id).order_by(FarmHistory.timestamp.asc()).all()
    # Serialize for frontend consumption
    data = [{
        'date': r.timestamp.strftime('%Y-%m-%d'),
        'water': r.water_amount or 0,
        'moisture': r.soil_moisture
    } for r in records]
    return render_template('analytics.html', chart_data=data)

@app.route('/history')
@login_required
def history():
    history_records = FarmHistory.query.filter_by(user_id=current_user.id).order_by(FarmHistory.timestamp.desc()).all()
    return render_template('history.html', history_records=history_records)

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/chatbot', methods=['POST'])
@login_required
def api_chatbot():
    user_message = request.json.get('message', '').lower()
    
    # Simple Rule-based NLP logic for farming queries
    response = "I'm AgroAI. I can help you with crop selection, irrigation practices, and water management. Could you provide more details?"
    
    if re.search(r'\b(less water|dry weather|drought)\b', user_message):
        response = "For dry weather or limited water availability, crops like Cotton, Sorghum, and Pearl Millet are excellent choices as they have lower water requirements and high drought tolerance."
    elif re.search(r'\b(often|how many times|when).*irrigate.*wheat\b', user_message):
        response = "Wheat generally requires 4-6 irrigations depending on soil type. The most critical stages are: CRI (20-25 days after sowing), tillering, late jointing, flowering, and dough stages."
    elif re.search(r'\b(best crop.*dry|dry area crop)\b', user_message):
        response = "Sorghum (Jowar), Pearl Millet (Bajra), and Pulses (like Chickpea/Gram) are the best crops for dry areas as they thrive with minimal rainfall."
    elif re.search(r'\b(rice|paddy).*water\b', user_message):
        response = "Rice is a water-intensive crop. It typically requires continuous submergence (about 5cm depth) during the vegetative stage and needs around 1200-1500 mm of water in total."
    elif re.search(r'\b(tomato|potatoes).*water\b', user_message):
        response = "Tomatoes and Potatoes need moderate water. Drip irrigation is highly recommended for these to prevent diseases caused by wet foliage while maintaining consistent soil moisture."
    elif re.search(r'\b(thank|thanks)\b', user_message):
        response = "You're welcome! Let me know if you need more agricultural advice."
    elif re.search(r'\b(hello|hi|hey)\b', user_message):
        response = f"Hello {current_user.farmer_name}! How can I assist you with your farming decisions today?"
        
    return jsonify({"response": response})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.farmer_name = request.form.get('farmer_name')
        current_user.farm_location = request.form.get('farm_location')
        farm_size = request.form.get('farm_size')
        current_user.farm_size = float(farm_size) if farm_size else None
        current_user.preferred_crops = request.form.get('preferred_crops')
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)
