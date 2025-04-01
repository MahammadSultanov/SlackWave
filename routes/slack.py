from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from utils.slack_utils import get_slack_client, get_channels, upload_file_to_slack
from slack_sdk.errors import SlackApiError
import os
import tempfile

slack_bp = Blueprint('slack', __name__)

@slack_bp.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    return render_template('index.html', username=username)

@slack_bp.route("/sms-sender", methods=["GET", "POST"])
def sms_sender():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    client = get_slack_client(session)
    
    if not client:
        return redirect(url_for('auth.login'))
    
    if request.method == "GET":
        try:
            # Get private and public channels
            private_response = client.conversations_list(types="private_channel")
            public_response = client.conversations_list(types="public_channel")
    
            # Extract the channels from the response
            private_channels = private_response.get("channels", [])
            public_channels = public_response.get("channels", [])
            
            # Create a set of private channel IDs for quick lookup
            private_channel_ids = {channel['id'] for channel in private_channels}
            
            # Combine channels and mark if they're private
            all_channels = []
            for channel in private_channels + public_channels:
                channel['is_private'] = channel['id'] in private_channel_ids
                all_channels.append(channel)
                
            return render_template("sms-sender.html", channels=all_channels, username=username)
        except SlackApiError as e:
            all_channels = []
            return render_template("sms-sender.html", channels=all_channels, username=username)

    # Handle the POST request
    selected_channels = request.form.getlist("channels")
    message = request.form.get("message")
    image = request.files.get("photo")

    if not selected_channels:
        return jsonify({"success": False, "message": "Please select at least one channel"})

    if not client:
        return jsonify({"success": False, "message": "Not authenticated"})

    message_errors = []
    if message:
        for channel_id in selected_channels:
            try:
                client.chat_postMessage(channel=channel_id, text=message)
            except SlackApiError as e:
                message_errors.append(f"Error sending to {channel_id}: {str(e)}")

    file_error = None
    if image and image.filename:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
            image.save(temp_file.name)
            success, msg = upload_file_to_slack(client, temp_file.name, selected_channels)
            if not success:
                file_error = msg
        os.unlink(temp_file.name)

    if message_errors or file_error:
        error_message = ". ".join(message_errors)
        if file_error:
            error_message += f" File upload error: {file_error}"
        return jsonify({"success": False, "message": error_message})
    
    return jsonify({"success": True, "message": "Message and files sent successfully"})

@slack_bp.route("/user-invite", methods=["GET"])
def user_invite():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    client = get_slack_client(session)
    
    if not client:
        return redirect(url_for('auth.login'))
    
    try:
        # Get private and public channels
        private_response = client.conversations_list(types="private_channel")
        public_response = client.conversations_list(types="public_channel")

        # Extract the channels from the response
        private_channels = private_response.get("channels", [])
        public_channels = public_response.get("channels", [])
        
        # Create a set of private channel IDs for quick lookup
        private_channel_ids = {channel['id'] for channel in private_channels}
        
        # Combine channels and mark if they're private
        all_channels = []
        for channel in private_channels + public_channels:
            channel['is_private'] = channel['id'] in private_channel_ids
            all_channels.append(channel)
            
        return render_template("user-invite.html", channels=all_channels, username=username)
    except SlackApiError as e:
        all_channels = []
        return render_template("user-invite.html", channels=all_channels, username=username)

@slack_bp.route("/add-to-channel", methods=["POST"])
def add_to_channel():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not authenticated"})
    
    client = get_slack_client(session)
    
    if not client:
        return jsonify({"success": False, "message": "Not authenticated"})
    
    # Get form data
    email = request.form.get("email")
    selected_channels = request.form.getlist("channels")

    if not email:
        return jsonify({"success": False, "message": "Please provide an email address"})
    
    if not selected_channels:
        return jsonify({"success": False, "message": "Please select at least one channel"})

    # First, try to get the user ID from the email
    try:
        user_info = client.users_lookupByEmail(email=email)
        user_id = user_info["user"]["id"]
        
        # Add user to each selected channel
        success_channels = []
        error_channels = []
        
        for channel_id in selected_channels:
            try:
                # Try to invite the user to the channel
                result = client.conversations_invite(
                    channel=channel_id,
                    users=[user_id]
                )
                success_channels.append(channel_id)
            except SlackApiError as e:
                error_channels.append(f"Channel {channel_id}: {str(e)}")
        
        if error_channels:
            return jsonify({
                "success": True, 
                "message": f"User added to {len(success_channels)} channels, with {len(error_channels)} errors: {', '.join(error_channels)}"
            })
        else:
            return jsonify({
                "success": True, 
                "message": f"User successfully added to {len(success_channels)} channels"
            })
            
    except SlackApiError as e:
        error_message = f"Error finding user: {str(e)}"
        return jsonify({"success": False, "message": error_message})