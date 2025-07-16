from flask import  request, jsonify, Flask
import psycopg2

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host = "localhost",
        port = "5432",
        database = "book_db",
        user = "norman",
        password = "097761"
    )
@app.route("/api/save-user-and-interests", methods=["POST"])

def save_user_and_interests():
    data = request.json
    google_user_id = data.get("id")
    name = data.get("name")
    email = data.get("email")
    interests = data.get("interests")

    if not google_user_id or not email or not name or not interests:
        return jsonify({"error" : "Missing required parameters"}), 400

    try:
        connection = get_connection()
        current = connection.cursor()

        current.execute(
            """
            INSERT INTO users (google_user_id, name, email)
            Values (%s, %s, %s)
            ON CONFLICT (google_user_id) DO UPDATE SET
            name = EXCLUDED.name, email = EXCLUDED.email
            RETURNING id;
            """,(google_user_id, name, email))
        user_id = current.fetchone()[0]
        current.execute("DELETE FROM user_intersets WHERE user_id = %s;", (user_id,))
        current.execute("""
                    INSERT INTO user_intersets (user_id, interests)
                    VALUES (%s, %s);
                """, (user_id, interests))

        connection.commit()
        current.close()
        connection.close()
        return jsonify({"message": "User and interests saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
