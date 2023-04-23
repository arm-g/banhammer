from flask import Flask, request
import json
from banhammer import BanHammer, Action

app = Flask(__name__)

bans = {
    "login_attempts": {
        "thresholds": [
            {
                "limit": 3,
                "window": 60,
                "action": [Action.block_local],
                "action_duration": 300
            }
        ]
    }
}

ban_hammer = BanHammer(bans)

def banhammer_protect(action, metric):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract the token from the request headers
            token = request.headers.get("Authorization")

            # Call the BanHammer instance to check if the token should be blocked
            blocked, stats = ban_hammer.incr(token, metric)

            # If the token is blocked, return an error response
            if blocked:
                return json.dumps({"error": "Too many login attempts. Please try again later."}), 429

            # Call the protected function
            result = func(*args, **kwargs)

            return result
        return wrapper
    return decorator

@app.route("/login", methods=["POST"])
@banhammer_protect(action=Action.block_local, metric="login_attempts")
def login():
    # Your login logic here
    return json.dumps({"message": "Logged in successfully."}), 200

if __name__ == "__main__":
    app.run()
