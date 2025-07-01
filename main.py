# main.py (Flask Backend for FreeSQLDatabase - MySQL)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import json
import os
import random
from datetime import datetime

app = Flask(__name__, static_folder='.') # Serve static files from the current directory
CORS(app) # Enable CORS for all routes

# --- FREE SQL DATABASE (MYSQL) CONNECTION DETAILS (IMPORTANT: DO NOT HARDCODE IN PRODUCTION) ---
# These will be loaded from PythonAnywhere's environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', '3306') # Default MySQL port, ensure it's a string

# Global variables (APP_ID is less critical for table naming here, but kept for consistency if needed elsewhere)
APP_ID = os.environ.get('__app_id', 'default-app-id')

def get_db_connection():
    """Establishes a new database connection."""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=int(DB_PORT) # Ensure port is an integer
        )
        print("Database connection successful.")
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Define the questions (MUST MATCH frontend - now 20 questions)
QUESTIONS = [
    {'id': 'q1', 'text': 'What was your family dynamic like?', 'type': 'multiple-choice', 'options': ['Supportive & Open', 'Strict & Traditional', 'Disconnected', 'Chaotic']},
    {'id': 'q2', 'text': 'Did you have a significant mentor in your life?', 'type': 'yes-no', 'options': ['Yes', 'No']},
    {'id': 'q3', 'text': 'Which value do you prioritize most?', 'type': 'multiple-choice', 'options': ['Honesty', 'Compassion', 'Freedom', 'Security']},
    {'id': 'q4', 'text': 'Do you believe people are inherently good?', 'type': 'yes-no', 'options': ['Yes', 'No']},
    {'id': 'q5', 'text': 'When solving a problem, what\'s your first step?', 'type': 'multiple-choice', 'options': ['Research', 'Brainstorm', 'Ask for help', 'Act quickly']},
    {'id': 'q6', 'text': 'Do you prefer detailed plans or spontaneous action?', 'type': 'multiple-choice', 'options': ['Detailed plans', 'Spontaneous action', 'Both', 'Neither']},
    {'id': 'q7', 'text': 'How do you react to criticism?', 'type': 'multiple-choice', 'options': ['Reflect & learn', 'Get defensive', 'Ignore it', 'Seek clarification']},
    {'id': 'q8', 'text': 'Are you more of an introvert or an extrovert?', 'type': 'multiple-choice', 'options': ['Introvert', 'Extrovert', 'Ambivert', 'Neither']},
    {'id': 'q9', 'text': 'What motivates you most?', 'type': 'multiple-choice', 'options': ['Personal growth', 'Helping others', 'Financial success', 'Recognition']},
    {'id': 'q10', 'text': 'Do you believe in destiny or free will?', 'type': 'yes-no', 'options': ['Destiny', 'Free Will']},
    # --- New Questions (11-20) ---
    {'id': 'q11', 'text': 'How do you typically handle stress?', 'type': 'multiple-choice', 'options': ['Exercise', 'Meditate', 'Talk to friends', 'Work harder']},
    {'id': 'q12', 'text': 'Are you generally optimistic or pessimistic?', 'type': 'multiple-choice', 'options': ['Optimistic', 'Pessimistic', 'Realistic', 'Depends']},
    {'id': 'q13', 'text': 'What role does creativity play in your life?', 'type': 'multiple-choice', 'options': ['Essential', 'Important', 'Minor', 'Not at all']},
    {'id': 'q14', 'text': 'Do you prefer working alone or in a team?', 'type': 'multiple-choice', 'options': ['Alone', 'Team', 'Both', 'Depends on task']},
    {'id': 'q15', 'text': 'How do you approach learning new things?', 'type': 'multiple-choice', 'options': ['Hands-on', 'Reading', 'Listening', 'Observing']},
    {'id': 'q16', 'text': 'Is routine important to you?', 'type': 'yes-no', 'options': ['Yes', 'No']},
    {'id': 'q17', 'text': 'How do you typically make big decisions?', 'type': 'multiple-choice', 'options': ['Logically', 'Intuitively', 'Consult others', 'Delay']},
    {'id': 'q18', 'text': 'What kind of challenges do you enjoy?', 'type': 'multiple-choice', 'options': ['Intellectual', 'Physical', 'Creative', 'Social']},
    {'id': 'q19', 'text': 'Do you learn more from success or failure?', 'type': 'multiple-choice', 'options': ['Success', 'Failure', 'Both equally', 'Neither']},
    {'id': 'q20', 'text': 'Is personal privacy very important to you?', 'type': 'yes-no', 'options': ['Yes', 'No']}
]

# Utility function to calculate similarity percentage
def calculate_similarity(user_answers, other_answers):
    if not user_answers or not other_answers:
        return 0.0

    matching_answers = 0
    total_questions = len(QUESTIONS)

    for q in QUESTIONS:
        user_ans = user_answers.get(q['id'])
        other_ans = other_answers.get(q['id'])

        if user_ans is not None and other_ans is not None and user_ans == other_ans:
            matching_answers += 1
    
    return (matching_answers / total_questions) * 100 if total_questions > 0 else 0.0

def create_tables():
    """Creates the necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        print("Could not connect to database to create tables.")
        return

    try:
        cur = conn.cursor()
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                social_media_platform VARCHAR(255),
                social_media_id VARCHAR(255),
                gender VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Answers table - one column per question for simplicity
        answers_columns = ", ".join([f"{q['id']} TEXT" for q in QUESTIONS])
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS answers (
                user_id VARCHAR(255) PRIMARY KEY,
                {answers_columns},
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        """)
        # Image Descriptions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS image_descriptions (
                user_id VARCHAR(255) PRIMARY KEY,
                description TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        """)
        # Favorites table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id VARCHAR(255) PRIMARY KEY,
                favorites_json TEXT NOT NULL, -- Storing as JSON string
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        print("Tables 'users', 'answers', 'image_descriptions', and 'favorites' checked/created successfully.")
    except Error as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def clear_all_data():
    """Deletes all data from the users, answers, image_descriptions, and favorites tables."""
    conn = get_db_connection()
    if conn is None:
        print("Could not connect to database to clear data.")
        return jsonify({"error": "Database not connected"}), 500

    try:
        cur = conn.cursor()
        # Delete from child tables first if there are foreign key constraints
        # (ON DELETE CASCADE should handle this, but explicit deletion is safer)
        cur.execute("DELETE FROM favorites;")
        cur.execute("DELETE FROM image_descriptions;")
        cur.execute("DELETE FROM answers;")
        cur.execute("DELETE FROM users;") # Delete from users last
        conn.commit()
        print("All data cleared successfully from 'users', 'answers', 'image_descriptions', and 'favorites' tables.")
        return jsonify({"message": "All data cleared successfully."}), 200
    except Error as e:
        print(f"Error clearing data: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# --- Routes for serving HTML pages ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/profile.html')
def serve_profile():
    return send_from_directory('.', 'profile.html')

@app.route('/questionnaire.html')
def serve_questionnaire():
    return send_from_directory('.', 'questionnaire.html')

@app.route('/image_description.html')
def serve_image_description():
    return send_from_directory('.', 'image_description.html')

@app.route('/favorites.html')
def serve_favorites():
    return send_from_directory('.', 'favorites.html')

@app.route('/comparison.html')
def serve_comparison():
    return send_from_directory('.', 'comparison.html')

@app.route('/one_to_one.html')
def serve_one_to_one():
    return send_from_directory('.', 'one_to_one.html')

@app.route('/global_compare.html')
def serve_global_compare():
    return send_from_directory('.', 'global_compare.html')

# --- API Endpoints ---
@app.route('/api/register_user', methods=['POST'])
def register_user():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.get_json()
    user_id = data.get('userId')
    name = data.get('name')
    email = data.get('email')
    social_media_platform = data.get('socialMediaPlatform')
    social_media_id = data.get('socialMediaId')
    gender = data.get('gender')

    if not all([user_id, name, email, gender]):
        return jsonify({"error": "Missing required profile data"}), 400

    try:
        cur = conn.cursor()
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert functionality
        cur.execute("""
            INSERT INTO users (user_id, name, email, social_media_platform, social_media_id, gender)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                email = VALUES(email),
                social_media_platform = VALUES(social_media_platform),
                social_media_id = VALUES(social_media_id),
                gender = VALUES(gender);
        """, (user_id, name, email, social_media_platform, social_media_id, gender))
        
        conn.commit()
        return jsonify({"message": "Profile saved successfully"}), 200
    except Error as e:
        print(f"Error saving profile: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/api/save_answers', methods=['POST'])
def save_answers():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json()
    user_id = data.get('userId')
    answers = data.get('answers')

    if not all([user_id, answers]):
        return jsonify({"error": "Missing required answer data"}), 400
    if len(answers) != len(QUESTIONS): # Check against the new 20 questions length
        return jsonify({"error": f"Incomplete answers provided. Expected {len(QUESTIONS)} questions, got {len(answers)}."}), 400

    try:
        cur = conn.cursor()
        # Dynamically build column names and values for the INSERT/UPDATE statement
        cols = ['user_id'] + [q['id'] for q in QUESTIONS]
        vals = [user_id] + [answers.get(q['id']) for q in QUESTIONS]
        
        # Build the ON DUPLICATE KEY UPDATE clause dynamically
        update_clauses = ", ".join([f"{col} = VALUES({col})" for col in cols if col != 'user_id'])
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert functionality
        placeholders = ", ".join(["%s"] * len(cols))
        insert_query = f"""
            INSERT INTO answers ({', '.join(cols)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clauses};
        """
        cur.execute(insert_query, vals)
        
        conn.commit()
        return jsonify({"message": "Answers saved successfully"}), 200
    except Error as e:
        print(f"Error saving answers: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/api/save_image_description', methods=['POST'])
def save_image_description():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.get_json()
    user_id = data.get('userId')
    image_description = data.get('imageDescription')

    if not all([user_id, image_description]):
        return jsonify({"error": "Missing required image description data"}), 400

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO image_descriptions (user_id, description)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                description = VALUES(description);
        """, (user_id, image_description))
        
        conn.commit()
        return jsonify({"message": "Image description saved successfully"}), 200
    except Error as e:
        print(f"Error saving image description: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/api/save_favorites', methods=['POST'])
def save_favorites():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.get_json()
    user_id = data.get('userId')
    favorites = data.get('favorites')

    if not all([user_id, favorites]):
        return jsonify({"error": "Missing required favorites data"}), 400
    
    try:
        cur = conn.cursor()
        favorites_json_str = json.dumps(favorites) # Convert dict to JSON string
        cur.execute("""
            INSERT INTO favorites (user_id, favorites_json)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                favorites_json = VALUES(favorites_json);
        """, (user_id, favorites_json_str))
        
        conn.commit()
        return jsonify({"message": "Favorites saved successfully"}), 200
    except Error as e:
        print(f"Error saving favorites: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/api/one_to_one_compare', methods=['POST'])
def one_to_one_compare():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.get_json()
    user_id = data.get('userId') # The currently logged-in user
    target_user_id = data.get('targetUserId') # Specific user to compare with (optional)
    user1_id_for_shared = data.get('user1Id') # For shared comparison links
    user2_id_for_shared = data.get('user2Id') # For shared comparison links

    try:
        cur = conn.cursor(dictionary=True) # Return results as dictionaries
        user1_answers = None
        user2_answers = None
        user1_profile = {}
        user2_profile = {}

        if user1_id_for_shared and user2_id_for_shared:
            # Case: Shared comparison link (comparing two specific users)
            cur.execute("SELECT * FROM answers WHERE user_id = %s", (user1_id_for_shared,))
            user1_answers_row = cur.fetchone()
            cur.execute("SELECT * FROM answers WHERE user_id = %s", (user2_id_for_shared,))
            user2_answers_row = cur.fetchone()

            if not user1_answers_row or not user2_answers_row:
                return jsonify({"error": "One or both users' answers not found for shared comparison"}), 404
            
            # Convert row to dict for easier access (assuming column names are 'q1', 'q2', etc.)
            user1_answers = {q['id']: user1_answers_row.get(q['id']) for q in QUESTIONS}
            user2_answers = {q['id']: user2_answers_row.get(q['id']) for q in QUESTIONS}

            cur.execute("SELECT name FROM users WHERE user_id = %s", (user1_id_for_shared,))
            user1_profile_row = cur.fetchone()
            user1_profile['name'] = user1_profile_row['name'] if user1_profile_row else 'User 1'

            cur.execute("SELECT name, social_media_platform, social_media_id FROM users WHERE user_id = %s", (user2_id_for_shared,))
            user2_profile_row = cur.fetchone()
            user2_profile = {
                'name': user2_profile_row['name'],
                'socialMediaPlatform': user2_profile_row['social_media_platform'],
                'socialMediaId': user2_profile_row['social_media_id']
            } if user2_profile_row else {'name': 'User 2'}

            percentage = calculate_similarity(user1_answers, user2_answers)
            return jsonify({
                "percentage": round(percentage, 2),
                "user1Name": user1_profile.get('name', 'User 1'),
                "otherUserName": user2_profile.get('name', 'User 2'),
                "user1Id": user1_id_for_shared,
                "otherUserId": user2_id_for_shared,
                "otherSocialMediaPlatform": user2_profile.get('socialMediaPlatform'),
                "otherSocialMediaId": user2_profile.get('socialMediaId')
            }), 200

        else:
            # Case: Regular one-to-one or random match for current user
            if not user_id:
                return jsonify({"error": "User ID is required for one-to-one comparison"}), 400

            cur.execute("SELECT * FROM answers WHERE user_id = %s", (user_id,))
            current_user_answers_row = cur.fetchone()
            if not current_user_answers_row:
                return jsonify({"error": "Current user's answers not found"}), 404
            current_user_answers = {q['id']: current_user_answers_row.get(q['id']) for q in QUESTIONS}

            other_user_id = target_user_id
            if not other_user_id:
                # Find a random other user who has submitted answers
                cur.execute("SELECT user_id FROM answers WHERE user_id != %s", (user_id,))
                eligible_user_ids = [row['user_id'] for row in cur.fetchall()]

                if not eligible_user_ids:
                    return jsonify({"message": "No other users with answers available for comparison yet."}), 200
                
                other_user_id = random.choice(eligible_user_ids)

            cur.execute("SELECT * FROM answers WHERE user_id = %s", (other_user_id,))
            other_user_answers_row = cur.fetchone()
            if not other_user_answers_row:
                return jsonify({"error": "Other user's answers not found"}), 404
            other_user_answers = {q['id']: other_user_answers_row.get(q['id']) for q in QUESTIONS}

            cur.execute("SELECT name, social_media_platform, social_media_id FROM users WHERE user_id = %s", (other_user_id,))
            other_user_profile_row = cur.fetchone()
            other_user_profile = {
                'name': other_user_profile_row['name'],
                'socialMediaPlatform': other_user_profile_row['social_media_platform'],
                'socialMediaId': other_user_profile_row['social_media_id']
            } if other_user_profile_row else {}

            percentage = calculate_similarity(current_user_answers, other_user_answers)

            return jsonify({
                "percentage": round(percentage, 2),
                "otherUserName": other_user_profile.get('name', 'Another User'),
                "otherUserId": other_user_id,
                "otherSocialMediaPlatform": other_user_profile.get('socialMediaPlatform'),
                "otherSocialMediaId": other_user_profile.get('socialMediaId')
            }), 200

    except Error as e:
        print(f"Error in one-to-one comparison: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/api/global_compare', methods=['POST'])
def global_compare():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json()
    user_id = data.get('userId')
    gender_filter = data.get('genderFilter', 'both')

    if not user_id:
        return jsonify({"error": "User ID is required for global comparison"}), 400

    try:
        cur = conn.cursor(dictionary=True) # Return results as dictionaries
        cur.execute("SELECT * FROM answers WHERE user_id = %s", (user_id,))
        current_user_answers_row = cur.fetchone()
        if not current_user_answers_row:
            return jsonify({"error": "Current user's answers not found"}), 404
        current_user_answers = {q['id']: current_user_answers_row.get(q['id']) for q in QUESTIONS}

        all_users_results = []
        
        # Build query for other users based on gender filter
        if gender_filter == 'both':
            cur.execute("""
                SELECT u.user_id, u.name, u.gender, u.social_media_platform, u.social_media_id, a.*
                FROM users u
                JOIN answers a ON u.user_id = a.user_id
                WHERE u.user_id != %s
            """, (user_id,))
        else:
            cur.execute("""
                SELECT u.user_id, u.name, u.gender, u.social_media_platform, u.social_media_id, a.*
                FROM users u
                JOIN answers a ON u.user_id = a.user_id
                WHERE u.user_id != %s AND u.gender = %s
            """, (user_id, gender_filter))
        
        other_users_data = cur.fetchall()

        for row in other_users_data:
            other_user_id = row['user_id']
            other_user_name = row['name']
            other_user_gender = row['gender']
            other_social_media_platform = row['social_media_platform']
            other_social_media_id = row['social_media_id']
            
            # Extract answers from the row dictionary
            other_user_answers = {q['id']: row.get(q['id']) for q in QUESTIONS}

            percentage = calculate_similarity(current_user_answers, other_user_answers)
            all_users_results.append({
                "userId": other_user_id,
                "name": other_user_name,
                "gender": other_user_gender,
                "percentage": round(percentage, 2),
                "socialMediaPlatform": other_social_media_platform,
                "socialMediaId": other_social_media_id
            })
        
        # Sort results by percentage descending
        all_users_results.sort(key=lambda x: x['percentage'], reverse=True)

        if not all_users_results:
            return jsonify({"message": "No other users found matching your criteria."}), 200

        return jsonify({"results": all_users_results}), 200

    except Error as e:
        print(f"Error in global comparison: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Temporary endpoint to clear all data - REMOVE OR SECURE IN PRODUCTION!
@app.route('/api/clear_all_data', methods=['POST'])
def clear_data_endpoint():
    # For security, you might want to add authentication or restrict this endpoint
    # to only be accessible from your IP address or via a secret key.
    print("Attempting to clear all data...")
    return clear_all_data()

if __name__ == '__main__':
    # Call create_tables to ensure tables exist on startup
    create_tables()
    # For local development, ensure you have mysql-connector-python installed:
    # pip install mysql-connector-python
    app.run(debug=False, port=5000) # Set debug to False for production
