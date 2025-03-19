from flask import Flask, session
from datetime import timedelta 
from routes.slack import slack_bp
from routes.auth import auth_bp
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.permanent_session_lifetime = timedelta(minutes=10)

#Registering the blueprints
app.register_blueprint(slack_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1453)
