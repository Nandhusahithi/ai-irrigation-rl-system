# AI-Driven Irrigation Decision Support System

A Full-Stack Web Application for a Final Year Computer Science Project demonstrating how Reinforcement Learning (Q-Learning) can optimize farm irrigation without IoT hardware.

## Project Overview

This dashboard allows farmers to input their farm conditions and receive data-driven irrigation recommendations. The system uses a Q-Learning Reinforcement Learning Model that processes historical and optimal crop data to generate intelligent decisions designed to conserve water and improve yield.

## Core Features
1. **Secure Authentication**: Farmer registration and profile management using Flask-Login and Bcrypt.
2. **Professional Dashboard**: Key statistics and a quick view of the latest AI decision, styled dynamically.
3. **Crop Selection Engine**: Specialized requirements pre-loaded for crops like Rice, Wheat, Maize, Cotton, Tomato, and Potato.
4. **Q-Learning RL Model**: The decision engine takes moisture, temp, and weather inputs and returns precise irrigation amounts (exploring/exploiting using a Q-Table).
5. **Interactive Analytics**: Dashboard and Analytics pages render beautiful charts using **Chart.js**.
6. **AgroAI Assistant**: A rule-based NLP chatbot for farming advisory.
7. **Farm History**: Data logging to an SQLite DB for tracking performance over the season.

## Tech Stack
- Frontend: HTML5, Tailwind CSS, Javascript, Chart.js
- Backend: Python 3, Flask, Flask-SQLAlchemy, Flask-Login
- AI Engine: Numpy, Pickle (Q-Learning)
- DB: SQLite

---

## Setup & Installation Instructions

### 1. Requirements
- Python 3.8+ installed on your computer.

### 2. Install Dependencies
Open a terminal in the project directory (`ai-irrigation-rl-system`) and run:
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database
The database is automatically created the first time you run the application. No manual migrations are necessary. The SQLite data will be saved to `database/irrigation.db`.

### 4. Run the Server
```bash
python app.py
```
After executing the script, open your web browser and navigate to:
**http://127.0.0.1:5000**

---

## Testing / Example Data

1. **Register a User**:
   - Name: John Doe
   - Email: john@example.com
   - Profile Data: Wheat, 10 Acres

2. **Test the Irrigation AI (Low moisture scenario)**:
   - Navigate to **Crop Selection**, select **Rice**.
   - Set Soil Moisture to **30%**.
   - Temperature: **32 C**
   - Weather: **Sunny**
   - Rain: **0**
   - *Result*: The AI will output an "Irrigate" decision along with a recommended water volume.

3. **Test the Irrigation AI (High moisture/Rainy scenario)**:
   - Select **Wheat**.
   - Set Soil Moisture to **70%**.
   - Set Weather: **Rainy**, Expected Rainfall: **20 mm**
   - *Result*: The AI will output "Do Not Irrigate" to prevent crop damage and save water.

4. **Analytics**:
   - Once you make a few decisions, go to **Analytics** to see the interactive charts populate with your history.

5. **Chatbot**:
   - Go to **AI Chatbot** and send: "How much water does rice need?" or "Which crop is best for dry weather?". You'll get instant advisory responses.
