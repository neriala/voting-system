from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
app = Flask(__name__)
CORS(app)  # אפשר תקשורת בין React ל-Flask


def is_valid_national_id(national_id):
    """בדיקה בסיסית לתוקף ת"ז (כולל ספרת ביקורת)."""
    if len(national_id) != 9 or not national_id.isdigit():
        return False

    total = sum(
        int(national_id[i]) * (2 if i % 2 == 0 else 1)
        for i in range(9)
    )
    return total % 10 == 0

@app.route('/authenticate', methods=['POST'])
def authenticate_voter():
    data = request.json
    national_id = data.get('national_id')

    if not national_id or not is_valid_national_id(national_id):
        return jsonify({'error': 'Invalid national ID'}), 400

    with sqlite3.connect("voting.db") as conn:
        voter = conn.execute("SELECT * FROM voters WHERE national_id = ?", (national_id,)).fetchone()
        if not voter:
            return jsonify({'error': 'Voter not found'}), 404

        if voter[2]:  # has_voted
            return jsonify({'error': 'You have already voted'}), 403

        return jsonify({'message': 'Authentication successful'}), 200


@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    national_id = data.get('national_id')
    vote = data.get('vote')

    #if not national_id or not is_valid_national_id(national_id):
     #   return jsonify({'error': 'Invalid national ID'}), 400

    with sqlite3.connect("voting.db") as conn:
        voter = conn.execute("SELECT * FROM voters WHERE national_id = ?", (national_id,)).fetchone()
        if not voter:
            return jsonify({'error': 'Voter not found'}), 404

        if voter[2]:  # has_voted
            return jsonify({'error': 'You have already voted'}), 403

        # עדכון מצביע להצבעה
        conn.execute("UPDATE voters SET has_voted = 1 WHERE national_id = ?", (national_id,))
        conn.commit()

    return jsonify({'message': f'Vote for {vote} received!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
