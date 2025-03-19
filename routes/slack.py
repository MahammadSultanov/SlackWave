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

@slack_bp.route("/user-invite", methods=["GET", "POST"])
def user_invite():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    client = get_slack_client(session)
    if request.method == "GET":
        channels = get_channels(client)
        return render_template("user-invite.html", channels=channels)

    email = request.form.get("email")
    full_name = request.form.get("full_name")
    welcome_message = request.form.get("message", "Welcome to our Slack workspace!")
    selected_channels = request.form.getlist("channels")
    
    if not email:
        return jsonify({"success": False, "error": "Email is required"})
    
    if not client:
        return jsonify({"success": False, "error": "Not authenticated with Slack"})
    
    try:
        response = client.admin_users_invite(
            email=email,
            channel_ids=selected_channels if selected_channels else None,
            custom_message=welcome_message,
            real_name=full_name,
            resend=True
        )
        return jsonify({"success": True})
    except SlackApiError as e:
        error_message = "Failed to invite user"
        response_data = getattr(e.response, "data", {})
        error = response_data.get("error")
        if error == "already_invited":
            error_message = "This user has already been invited"
        elif error == "already_in_team":
            error_message = "This user is already in your workspace"
        elif error == "invalid_email":
            error_message = "Invalid email address"
        elif error == "not_admin":
            error_message = "You don't have admin permissions to invite users"
        return jsonify({"success": False, "error": error_message})

@slack_bp.route("/sms-sender", methods=["GET", "POST"])
def sms_sender():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    client = get_slack_client(session)
    
    if request.method == "GET":
        channels = get_channels(client)
        return render_template("sms-sender.html", channels=channels, username=username)

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