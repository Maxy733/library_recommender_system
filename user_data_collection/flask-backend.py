from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "book_db",
    "user": "norman",
    "password": "097761"
}

def get_connection():
    """Create and return a database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                google_user_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create user_interests table (fixed typo from 'user_intersets')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                interests TEXT[] NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_google_id 
            ON users(google_user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_interests_user_id 
            ON user_interests(user_id);
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

@app.route('/api/save-user-and-interests', methods=['POST'])
def save_user_and_interests():
    """Save or update user information and their interests"""
    try:
        data = request.json
        print("Received data:", data)
        google_user_id = data.get("id")
        name = data.get("name")
        email = data.get("email")
        interests = data.get("interests")

        # Validate required fields
        if not google_user_id or not email or not name:
            return jsonify({"error": "Missing required user information"}), 400
        
        if not interests or not isinstance(interests, list):
            return jsonify({"error": "Interests must be provided as a list"}), 400

        connection = get_connection()
        cursor = connection.cursor()

        try:
            # Begin transaction
            connection.autocommit = False
            
            # Insert or update user
            cursor.execute("""
                INSERT INTO users (google_user_id, name, email, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (google_user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """, (google_user_id, name, email))
        
            print("User inserted or updated successfully")
            user_id = cursor.fetchone()[0]
            
            # Delete existing interests for the user
            cursor.execute("""
                DELETE FROM user_interests WHERE user_id = %s;
            """, (user_id,))
            
            # Insert new interests
            cursor.execute("""
                INSERT INTO user_interests (user_id, interests, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP);
            """, (user_id, interests))
            
            # Commit transaction
            connection.commit()
            
            return jsonify({
                "message": "User and interests saved successfully",
                "user_id": user_id,
                "interests_count": len(interests)
            }), 200
            
        except Exception as e:
            # Rollback transaction on error
            connection.rollback()
            raise e
            
        finally:
            cursor.close()
            connection.close()
        
    except Exception as e:
        print("❌ ERROR during /api/save-user-and-interests:", str(e))
        return jsonify({"error": str(e)}), 500

    except psycopg2.IntegrityError as e:
        return jsonify({"error": "Database integrity error", "details": str(e)}), 400
    except psycopg2.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.route("/api/get-preferences/<google_user_id>", methods=["GET"])
def get_preferences(google_user_id):
    """Get user preferences by Google user ID"""
    try:
        if not google_user_id:
            return jsonify({"error": "User ID is required"}), 400

        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Get user and their interests
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.google_user_id,
                   ui.interests, ui.updated_at as interests_updated_at
            FROM users u
            LEFT JOIN user_interests ui ON u.id = ui.user_id
            WHERE u.google_user_id = %s;
        """, (google_user_id,))

        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if not result:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "id": result['google_user_id'],
            "name": result['name'],
            "email": result['email'],
            "interests": result['interests'] or [],
            "last_updated": result['interests_updated_at'].isoformat() if result['interests_updated_at'] else None
        }), 200

    except psycopg2.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        connection.close()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route("/api/users/stats", methods=["GET"])
def get_user_stats():
    """Get statistics about users and interests"""
    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Get total users
        cursor.execute("SELECT COUNT(*) as total_users FROM users;")
        total_users = cursor.fetchone()['total_users']

        # Get most popular interests
        cursor.execute("""
            SELECT interest, COUNT(*) as count
            FROM (
                SELECT unnest(interests) as interest
                FROM user_interests
            ) as all_interests
            GROUP BY interest
            ORDER BY count DESC
            LIMIT 10;
        """)
        popular_interests = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify({
            "total_users": total_users,
            "popular_interests": popular_interests
        }), 200

    except psycopg2.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Initialize database on startup
    try:
        init_database()
        print("Starting Flask server on port 5000...")
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        print(f"Failed to start server: {e}")