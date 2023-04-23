from flask import Flask, jsonify, request
from banhammer import BanHammer, Action

app = Flask(__name__)

# Initialize BanHammer with bans configuration
bans = {
    "login_attempts": {
        "thresholds": [
            {
                "window": 60,
                "limit": 3,
                "action": [Action.block_local, Action.record_local],
                "action_duration": 600
            },
            {
                "window": 3600,
                "limit": 10,
                "action": [Action.report_central],
                "action_duration": None
            }
        ]
    }
}

banhammer = BanHammer(bans=bans, return_rates=True)

@app.route("/login", methods=["POST"])
def login():
    token = request.form.get("token")

    # Check if the token has exceeded any thresholds and take appropriate action
    passed, stats = banhammer.incr(token=token, metric="login_attempts")

    # If the token should be blocked, return an error response
    if not passed:
        return jsonify({"error": "Too many login attempts. Please try again later."}), 429

    # If the token is allowed to login, return a success response
    return jsonify({"message": "Login successful.", "stats": stats}), 200

if __name__ == "__main__":
    app.run()
