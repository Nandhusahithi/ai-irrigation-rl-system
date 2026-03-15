import numpy as np
import os
import pickle

class IrrigationQLearning:
    def __init__(self, load_path=None):
        # Actions: 
        # 0: Do not irrigate (0L)
        # 1: Irrigate Low (e.g., maintain minimum moisture)
        # 2: Irrigate Standard (optimal for crop)
        # 3: Irrigate High (if severe deficit)
        self.num_actions = 4
        
        # State space discretization
        # We discretize the continuous values to create a tabular state space
        # Moisture: Low (0), Optimal (1), High (2)
        # Temperature: Cool (0), Normal (1), Hot (2)
        # Rainfall: None (0), Light (1), Heavy (2)
        # 3 * 3 * 3 = 27 states
        self.num_states_moisture = 3
        self.num_states_temp = 3
        self.num_states_rain = 3
        
        # Initialize Q-table (States x Actions)
        # Shape: (3, 3, 3, 4)
        if load_path and os.path.exists(load_path):
            with open(load_path, 'rb') as f:
                self.q_table = pickle.load(f)
        else:
            # Random initialization, slightly optimistic for standard irrigation to encourage exploration
            self.q_table = np.random.uniform(low=0.0, high=1.0, size=(
                self.num_states_moisture, 
                self.num_states_temp, 
                self.num_states_rain, 
                self.num_actions
            ))
            
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1 # Exploration rate
        
        # Crop optimal ranges (Moisture %, Water req per session in Liters)
        self.crop_specs = {
            'Rice': {'optimal_moisture': 80, 'water_standard': 300},
            'Wheat': {'optimal_moisture': 50, 'water_standard': 150},
            'Maize': {'optimal_moisture': 60, 'water_standard': 200},
            'Cotton': {'optimal_moisture': 40, 'water_standard': 120},
            'Tomato': {'optimal_moisture': 65, 'water_standard': 100},
            'Potato': {'optimal_moisture': 70, 'water_standard': 110}
        }

    def _discretize_state(self, crop, moisture, temp, rainfall):
        """Convert continuous sensor/input data into discrete state indices."""
        # Baseline moisture logic
        optimal_m = self.crop_specs.get(crop, {'optimal_moisture': 50})['optimal_moisture']
        
        if moisture < optimal_m - 15:
            m_state = 0 # Low
        elif moisture > optimal_m + 15:
            m_state = 2 # High
        else:
            m_state = 1 # Optimal
            
        # Temperature logic
        if temp < 20:
            t_state = 0 # Cool
        elif temp > 32:
            t_state = 2 # Hot
        else:
            t_state = 1 # Normal
            
        # Rainfall logic
        if rainfall == 0:
            r_state = 0 # None
        elif rainfall < 10:
            r_state = 1 # Light
        else:
            r_state = 2 # Heavy
            
        return (m_state, t_state, r_state)

    def predict_action(self, crop, moisture, temp, rainfall, exploit_only=True):
        """Choose best action based on Q-table or epsilon-greedy if exploring."""
        state = self._discretize_state(crop, moisture, temp, rainfall)
        
        if not exploit_only and np.random.uniform(0, 1) < self.epsilon:
            action = np.random.choice(self.num_actions)
        else:
            action = np.argmax(self.q_table[state])
            
        return action, state

    def calculate_reward(self, crop, moisture, rainfall, action):
        """Simulate a reward based on the action taken."""
        optimal_m = self.crop_specs.get(crop, {'optimal_moisture': 50})['optimal_moisture']
        
        # Determine logical appropriateness of action
        m_state = self._discretize_state(crop, moisture, 25, rainfall)[0]
        r_state = self._discretize_state(crop, moisture, 25, rainfall)[2]
        
        reward = 0
        
        if m_state == 0: # Dry soil
            if action == 0: # Did not irrigate when needed
                reward = -10
            elif action == 3 and r_state == 2: # Heavy rain expected but still irrigated highly
                reward = -5
            elif action == 2: # Standard irrigation
                reward = 10
            else:
                reward = 5
                
        elif m_state == 1: # Optimal soil
            if action == 0 and r_state == 0: # Didn't irrigate, but no rain
                reward = 5 # Good conservative play
            elif action > 0: # Irrigated unnecessarily
                reward = -5 * action
            else:
                reward = 10
                
        elif m_state == 2: # High moisture
            if action > 0: # Irrigated when already wet
                reward = -10 * action
            else:
                reward = 10
                
        return reward

    def update_q_table(self, old_state, action, reward, new_state):
        """Update Q values based on the action taken and reward received."""
        old_q = self.q_table[old_state][action]
        next_max = np.max(self.q_table[new_state])
        
        # Q-learning formula
        new_q = (1 - self.learning_rate) * old_q + self.learning_rate * (reward + self.discount_factor * next_max)
        self.q_table[old_state][action] = new_q

    def save_model(self, save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            pickle.dump(self.q_table, f)

    def get_recommendation(self, crop, moisture, temp, rainfall):
        """Wrapper for API/Dashboard to get a user-friendly recommendation."""
        action, state = self.predict_action(crop, moisture, temp, rainfall, exploit_only=True)
        
        # Just quickly simulate a learning step to "improve" on the fly for demonstration
        reward = self.calculate_reward(crop, moisture, rainfall, action)
        
        base_water = self.crop_specs.get(crop, {'water_standard': 150})['water_standard']
        
        decision = 'Irrigate' if action > 0 else 'Do not irrigate'
        
        if action == 0:
            water_amount = 0
        elif action == 1:
            water_amount = base_water * 0.5
        elif action == 2:
            water_amount = base_water
        elif action == 3:
            water_amount = base_water * 1.5
            
        return {
            'decision': decision,
            'water_amount': int(water_amount),
            'action_index': int(action),
            'simulated_reward': float(reward),
            'state_tuple': state
        }
