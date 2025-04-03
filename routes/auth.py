from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from utils.auth import get_user_data, save_user_data
from werkzeug.security import check_password_hash, generate_password_hash
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.password_validator import validate_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user_data = get_user_data(username)
    if not user_data or not check_password_hash(user_data['password'], password):
        return jsonify({"message": "Invalid username or password"}), 401
    
    session.permanent = True
    session['username'] = username
    return jsonify({"message": "Login successful"})


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    slack_token = data.get('slack_token')
    
    if not all([username, password, slack_token]):
        return jsonify({"message": "All fields are required"}), 400
    
    # Validate password
    is_valid, error_message = validate_password(password)
    if not is_valid:
        return jsonify({"message": error_message}), 400
    
    # Check if username already exists
    if get_user_data(username):
        return jsonify({"message": "Username already exists"}), 409
    
    # Verify the Slack token is valid
    try:
        test_client = WebClient(token=slack_token)
        test_client.auth_test()
    except SlackApiError:
        return jsonify({"message": "Invalid Slack token"}), 400
    
    hashed_password = generate_password_hash(password)
    if save_user_data(username, hashed_password, slack_token):
        session['username'] = username
        return jsonify({"message": "User created successfully"}), 201
    else:
        return jsonify({"message": "Error creating user"}), 500

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    print(session)
    return redirect(url_for('auth.login'))