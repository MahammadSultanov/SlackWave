from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import tempfile
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import pandas as pd

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

def get_user_data(username):
    try:
        df = pd.read_csv('users.csv')
        user = df[df['username'] == username].to_dict('records')
        if user:
            return user[0]
        return None
    except Exception as e:
        print(f"Error reading user data: {e}")
        return None

def save_user_data(username, password_hash, slack_token):
    try:
        new_user = {
            'username': username,
            'password': password_hash,
            'slack_token': slack_token
        }
        try:
            df = pd.read_csv('users.csv')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['username', 'password', 'slack_token'])
        
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_csv('users.csv', index=False)
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False

def get_slack_client():
    if 'username' in session:
        user_data = get_user_data(session['username'])
        print(f"Getting Slack client for user: {session['username']}")
        if user_data and user_data['slack_token']:
            return WebClient(token=user_data['slack_token'])
        else:
            print("No Slack token found for user")
    else:
        print("No user in session")
    return None

def get_channels():
    client = get_slack_client()
    if not client:
        print("No Slack client available")
        return []
    
    try:
        response = client.conversations_list(types="private_channel,public_channel")
        channels = response["channels"]
        return [{"id": channel["id"], "name": channel["name"]} for channel in channels]
    except SlackApiError as e:
        print(f"Error getting channels: {e}")
        return []
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user_data = get_user_data(username)
    if not user_data or not check_password_hash(user_data['password'], password):
        return jsonify({"message": "Invalid username or password"}), 401
    
    session['username'] = username
    return jsonify({"message": "Login successful"})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    slack_token = data.get('slack_token')
    
    if not all([username, password, slack_token]):
        return jsonify({"message": "All fields are required"}), 400
    
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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html')
@app.route("/sms-sender", methods=["GET", "POST"])
def sms_sender():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == "GET":
        channels = get_channels()
        return render_template("sms-sender.html", channels=channels)

    # Handle POST request
    try:
        selected_channels = request.form.getlist("channels")
        message = request.form["message"]
        image = request.files.get("photo")

        if not selected_channels:
            return jsonify({"success": False, "message": "Please select at least one channel"})

        client = get_slack_client()
        if not client:
            return jsonify({"success": False, "message": "Not authenticated"})

        # Send messages to all selected channels
        message_errors = []
        for channel_id in selected_channels:
            try:
                if message:
                    client.chat_postMessage(channel=channel_id, text=message)
            except SlackApiError as e:
                message_errors.append(f"Error sending message to channel {channel_id}: {str(e)}")

        # Handle file upload if present
        file_error = None
        if image and image.filename:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
                    image.save(temp_file.name)
                    upload_success, upload_message = upload_file_to_slack(temp_file.name, selected_channels)
                    if not upload_success:
                        file_error = upload_message
                os.unlink(temp_file.name)
            except Exception as e:
                file_error = str(e)

        # Prepare response
        if message_errors or file_error:
            error_message = ". ".join(message_errors)
            if file_error:
                error_message += f" File upload error: {file_error}"
            return jsonify({"success": False, "message": error_message})

        return jsonify({"success": True, "message": "Message and files sent successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({"message": "Not logged in"}), 401

    client = get_slack_client()
    if not client:
        return jsonify({"message": "No Slack client available"}), 400

    channels = request.form.getlist('channels')
    message = request.form.get('message', '').strip()
    
    if not channels:
        return jsonify({"message": "No channels selected"}), 400
    
    if not message and 'photo' not in request.files:
        return jsonify({"message": "Please provide a message or file"}), 400

    try:
        # Send message if provided
        if message:
            for channel in channels:
                client.chat_postMessage(
                    channel=channel,
                    text=message
                )

        # Upload file if provided
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, file.filename)
                file.save(temp_path)
                try:
                    success, msg = upload_file_to_slack(temp_path, channels)
                    if not success:
                        return jsonify({"message": f"Error uploading file: {msg}"}), 500
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        return jsonify({"message": "Message sent successfully"}), 200
    
    except SlackApiError as e:
        return jsonify({"message": f"Error sending message: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

def upload_file_to_slack(file_path, channel_ids):
    client = get_slack_client()
    if not client:
        return False, "Not authenticated"
    
    try:
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as file:
            for channel_id in channel_ids:
                try:
                    response = client.files_upload_v2(
                        channel=channel_id,
                        file=file,
                        filename=os.path.basename(file_path),
                        length=file_size
                    )
                    file.seek(0)
                except SlackApiError as e:
                    print(f"Error uploading file to channel {channel_id}: {e}")
                    return False, str(e)
        return True, "File uploaded successfully"
    except Exception as e:
        print(f"Error in file upload: {e}")
        return False, str(e)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1453)
