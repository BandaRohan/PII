import json
from random import randint
import subprocess
from zipfile import ZipFile
from flask import Flask, flash, render_template, request, redirect, send_from_directory, url_for, session
import numpy as np
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import cv2 as cv
import random
import string
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
from bson import ObjectId
from face_detection import detect_faces
from face_detection import usr_encoding
import uuid
from face_detection import cosine_similarity
app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['user_database']
users_collection = db['users']
groups_collection = db['grps']
user_matched_images_collection = db['matched_images']
images_collection = db['Group_img']
# Add this line to your MongoDB configuration section
user_images_collection = db['user_images']

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure the upload folder for profile pictures
app.config['UPLOAD_FOLDER'] = ''

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ...
from flask import jsonify, request


@app.route('/')
def index():
    if 'username' in session:
        # first_name = session.get('first_name', '')
        # last_name = session.get('last_name', '')
        # return f'Logged in as {first_name} {last_name}! <br><a href="/logout">Logout</a>'
        return render_template('index.html')
    return 'You are not logged in <br><a href="/login">Login</a>'
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
    # If the user is already logged in, redirect to the dashboard or profile page
        redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if not users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
            users_collection.insert_one({
                'username': username,
                'email': email,
                'password': hashed_password,
                'first_name': first_name,
                'last_name': last_name
            })
            return redirect(url_for('login'))
        else:
            return 'Username or email already exists. Please choose different ones.'

    return render_template('signup.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None  # Initialize the error message

    if "email" in session:
        message = "You are already logged in. Please log out first to log in to another account."
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        identifier = request.form.get('identifier')  # Change this to match your form field name
        password = request.form['password']

        user = users_collection.find_one({
            '$or': [
                {'username': identifier},
                {'email': identifier}
            ]
        })

        # After successful login
        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['email'] = user['email']
            return redirect(url_for('index'))
        else:
            error_message = 'Invalid email/username or password'

    return render_template('login.html', error_message=error_message)


from flask_mail import Mail, Message
import secrets

# Initialize Flask-Mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_mail import Mail, Message  # Import Flask-Mail

# Add Flask-Mail configuration
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bandarohan65@gmail.com'
app.config['MAIL_PASSWORD'] = 'nilp tyqs qjdv rwrp'

def generate_otp():
    return str(randint(1000, 9999))

def send_otp_email(email, otp):
    msg = Message('Password Reset OTP', recipients=[email])
    msg.body = f'Your OTP for password reset is: {otp}'
    mail.send(msg)

# Route for sending OTP email
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({'email': email})
        if user:
            # Generate OTP
            otp = generate_otp()
            # Save the OTP in the database or associate it with the user's record
            users_collection.update_one({'email': email}, {'$set': {'reset_otp': otp}})
            # Send OTP to user's email
            send_otp_email(email, otp)
            flash('An OTP has been sent to your email. Please check your inbox.', 'success')
            return redirect(url_for('verify_otp'))
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_entered = request.form['otp']
        email = request.form['email']
        user = users_collection.find_one({'email': email})
        if user and 'reset_otp' in user and user['reset_otp'] == otp_entered:
            # Valid OTP, allow password reset
            return redirect(url_for('reset_password', email=email))
        else:
            flash('Invalid OTP. Please try again.', 'error')
    return render_template('verify_otp.html')


# Update the reset_password route to include email parameter
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            # Update the password in the database
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            users_collection.update_one({'email': email}, {'$set': {'password': hashed_password, 'reset_otp': None}})
            flash('Password reset successfully. You can now login with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.', 'error')
    return render_template('reset_password.html')


# Modify your dashboard route to render the dashboard template
def load_known_embeddings():
    known_embeddings = []
    # Query your database to retrieve known embeddings
    known_faces = user_images_collection.find({})

    for face in known_faces:
        known_embeddings.append({
            'email': face['email'],
            'encodings': face['encodings']
        })

    return known_embeddings


from flask import Response
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session:
        user_info = {
            'username': session['username'],
            'first_name': session['first_name'],
            'last_name': session['last_name'],
            'email': session.get('email', '')  # Use get() with a default value
        }

        # Initialize profile_picture to None
        profile_picture = None

        # Load embeddings of known faces from the database
        known_embedding = load_known_embeddings()

        # Return the live video stream as a response
        # return Response(start_video(known_embedding), mimetype='multipart/x-mixed-replace; boundary=frame')
        return render_template('dashboard.html',user_info=user_info)    
        
import cv2

@app.route('/start_camera')
def start_camera():
    return redirect(url_for('start_video'))
from flask import redirect, url_for

from flask import Response

@app.route('/start_video')
def start_video():
    def generate():
        # Load embeddings of known faces from the database
        known_embedding = load_known_embeddings()

        camera = cv2.VideoCapture(0)
        while True:
            ret, frame = camera.read()
            if not ret:
                break

            # Your face recognition logic here
            face_locations = fr.face_locations(frame)
            if len(face_locations) > 0:
                face_encodings = fr.face_encodings(frame, face_locations)
                for i, face_encoding in enumerate(face_encodings):
                    max_score = 0
                    recognized_person = None

                    for entry in known_embedding:
                        stored_face_encodings = entry['encodings']
                        similarity_score = cosine_similarity(face_encoding.reshape(1, -1), np.array(stored_face_encodings))
                        current_max_score = np.max(similarity_score)
                        if current_max_score > max_score:
                            max_score = current_max_score
                            recognized_person = entry['email']

                    if max_score > 0.95:
                        # Draw bounding box around the face
                        top, right, bottom, left = face_locations[i]
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        # Put recognized person's email as text on the bounding box
                        cv2.putText(frame, recognized_person, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            # Convert frame to JPEG format
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        camera.release()

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Define the route to serve profile pictures
@app.route('/profile_pictures/<filename>')
def get_profile_picture(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/profile_info', methods=['GET', 'POST'])
def profile_info():
    if 'username' in session:
        user_info = {
            'username': session['username'],
            'first_name': session['first_name'],
            'last_name': session['last_name'],
            'email': session.get('email', '')
        }
        profile_picture = None
        profile_picture_uploaded = False  # Initialize profile picture upload status
        
        # Handle profile picture upload
        if request.method == 'POST':
            file = request.files['profile_picture']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                # Check if there's an existing profile picture for the user
                existing_image = user_images_collection.find_one({'email': session.get('email', '')})

                # Save the image to the upload folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image = cv.imread(file_path)
                face_locations = detect_faces(file_path)

                # Check the number of faces detected
                if len(face_locations) != 1:
                    # Delete the uploaded file if there are more or less than one face
                    os.remove(file_path)
                    flash('Please select another image with exactly one face.', 'error')
                    return redirect(url_for('profile_info'))  # Redirect to the profile_info page
                else:
                    usr_encodings = usr_encoding(image, face_locations)

                if existing_image:
                    if len(face_locations) == 1:
                        # Delete the existing image from the database
                        user_images_collection.delete_one({'email': session['email']})

                # Save the image in the database
                user_images_collection.insert_one(
                    {'email': session['email'],
                     'filename': file_path,
                     'encodings': usr_encodings
                     })

                profile_picture_uploaded = True  # Set profile picture upload status to true

                flash('Profile picture uploaded successfully.', 'success')  # Flash success message

        # Retrieve profile picture filename for the user
        profile_picture = user_images_collection.find_one({'email': session.get('email', '')})

        return render_template('profile_info.html', user_info=user_info, profile_picture=profile_picture, profile_picture_uploaded=profile_picture_uploaded)

    else:
        return redirect(url_for('login'))



def generate_unique_code():
    # Generate a random 6-character unique code (combination of digits and letters)
    unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Check if the code is already in use, and regenerate if necessary
    while groups_collection.find_one({'unique_code': unique_code}):
        unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    return unique_code


@app.route('/create_group', methods=['POST'])
def create_group():
    group_name = request.json.get('groupName')
    if group_name:
        unique_code = generate_unique_code()

        # Assuming you have a MongoDB collection named 'groups'
        # Add the current user's email as a member
        groups_collection.insert_one({
            'name': group_name,
            'unique_code':unique_code,
            'members': [session.get('email', '')]
        })
        return jsonify(status='success')
    return jsonify(status='failure', message='Invalid group name')

# ...

@app.route('/get_user_groups_with_names', methods=['GET'])
def get_user_groups_with_names():
    if 'username' in session:
    # Assuming you have a MongoDB collection named 'groups'
    # Fetch groups where the current user is a member
        user_email = session.get('email', '')
        user_groups = groups_collection.find({'members': user_email})

        # Create a list of dictionaries containing group names and unique codes
        groups_with_names = [{'name': user_group['name'], 'unique_code': user_group['unique_code']} for user_group in user_groups]

        return jsonify(groups_with_names)

def load_embeddings(group_unique_code):
    data = []
    group_members = groups_collection.find_one({'unique_code': group_unique_code})
    if group_members:
        usr_emails = group_members['members']
        for email in usr_emails:
            user_data = user_images_collection.find_one({'email': email})
            if user_data:
                data.append(user_data)
    return data


import face_recognition as fr
from PIL import Image

app.config['UPLOAD_FOLDER'] = 'uploads'
@app.route('/upload_images', methods=['GET', 'POST'])
def upload_images():
    if user_images_collection.find_one({'email': session['email']}):
        pass
    else:
        return redirect(url_for('profile_info'))
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        group_unique_code = request.form.get('group')
        uploaded_images = request.files.getlist('images')
        group = groups_collection.find_one({'unique_code': group_unique_code})
        known_embedding = load_embeddings(group_unique_code)
        
        # print(known_embedding)
        # print(type(load_embeddings))
                
        if group:
            for image in uploaded_images:
                if image and allowed_file(image.filename):
                    # Generate a UUID for the image
                    image_uuid = str(uuid.uuid4())

                    # Save the image to the server
                    filename = secure_filename(image.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(file_path)

                    with open(file_path, 'rb') as image_file:
                        image_data = image_file.read()
                    

                    # Save the file path in MongoDB along with the group name and image UUID
                    images_collection.insert_one({
                        'unique_code': group_unique_code,
                        'group_name': group['name'],
                        'filename': filename,
                        'file_path': file_path,
                        'data': image_data,
                        'image_uuid': image_uuid
                    })

    
                    for user_image_path in [file_path]:
                        target_images = fr.load_image_file(user_image_path)
                        target_location = fr.face_locations(target_images)
                        print("Length:", len(target_location))
                        target_encodings = fr.face_encodings(target_images, target_location)
                        user_image_name = (user_image_path.split("/")[-1]).split(".")[0]

                        if not target_encodings:
                            print(f"No faces found in {user_image_path}")
                            continue

                        for i, target_encoding in enumerate(target_encodings):
                            max_score = 0
                            recognized_person = None
                            faces = target_location[i]

                            for entry in known_embedding:
                                stored_face_encodings = entry['encodings']
                                similarity_score = cosine_similarity(target_encoding.reshape(1, -1), np.array(stored_face_encodings))
                                print(similarity_score)
                                current_max_score = np.max(similarity_score)
                                if current_max_score > max_score:
                                    max_score = current_max_score
                                    recognized_person = entry['email']
                            print(f'max score is:{max_score} of {user_image_name} and recognized as {recognized_person}')

                            if max_score > 0.90:
                                print(f"{user_image_name} is identified as {recognized_person}")

                                user_matched_images_collection.update_one(
                                    {'email': recognized_person, 'group_unique_code': group_unique_code},
                                    {'$addToSet': {'matched_images_uuid': image_uuid}},
                                    upsert=True
                                )
                            else:
                                print("NO match found")
                
                else:
                    flash(f"Invalid file extension for {image.filename}. Supported formats: jpeg, jpg, png, gif", 'error')

                # print(usr_email)
            flash('Images uploaded successfully.', 'upload_images')
            return redirect(url_for('upload_images', group=group_unique_code, group_name=group['name']))

    group_unique_code = request.args.get('group', '')
    group = groups_collection.find_one({'unique_code': group_unique_code})
    images = images_collection.find({'unique_code': group_unique_code})
    current_user_email = session.get('email', '')
    my_images_group = user_matched_images_collection.find_one({'group_unique_code': group_unique_code, 'email': current_user_email})

    matched_images = []
    if my_images_group:
        uuids = my_images_group.get('matched_images_uuid', [])
        for image_uuid in uuids:
            matched_image = images_collection.find_one({'image_uuid': image_uuid})
            if matched_image:
                matched_images.append(matched_image)

    return render_template('upload_images.html', group=group_unique_code, group_name=group['name'], images=images, matched_images=matched_images)


app.config['UPLOAD_FOLDER']=''
@app.route('/uploaded_images/<filename>')
def get_uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def get_image_path(image_uuid):
    image_data = images_collection.find_one({'image_uuid': image_uuid})
    if image_data:
        return image_data['file_path']
    else:
        return None

@app.route('/share_group/<group_code>', methods=['GET'])
def share_group(group_code):
    # Render the upload_images page with the group code
    return render_template('upload_images.html', group_code=group_code)

@app.route('/join_group', methods=['POST'])
def join_group():
    group_code = request.json.get('groupCode')
    if group_code:
        group = groups_collection.find_one({'unique_code': group_code})
        if group:
            user_email = session.get('email', '')
            if user_email not in group['members']:
                groups_collection.update_one({'unique_code': group_code}, {'$push': {'members': user_email}})
                known_embeddings = load_embeddings(group_code)
                if known_embeddings:
                    file_paths = images_collection.find({'unique_code': group_code})

                    for file_path_obj in file_paths:
                        image_uuid = file_path_obj['image_uuid']
                        print(image_uuid)
                        file_path =file_path_obj['file_path']
                        print(file_path)
                        target_image = fr.load_image_file(file_path)
                        target_locations = fr.face_locations(target_image)
                        target_encodings = fr.face_encodings(target_image, target_locations)
                        if not target_encodings:
                            print(f"No faces found in {file_path}")
                            continue
                        for i, target_encoding in enumerate(target_encodings):
                            max_score = 0
                            recognized_person = None
                            faces = target_locations[i]

                            for entry in known_embeddings:
                                stored_face_encodings = entry['encodings']
                                similarity_score = cosine_similarity(target_encoding.reshape(1, -1), np.array(stored_face_encodings))
                                print(similarity_score)
                                current_max_score = np.max(similarity_score)
                                if current_max_score > max_score:
                                    max_score = current_max_score
                                    recognized_person = entry['email']
                            print(f'max score is:{max_score} of {file_path} and recognized as {recognized_person}')

                            if max_score > 0.90:  # Adjust threshold as needed
                                print(f"{file_path} is identified as {recognized_person}")
                                user_matched_images_collection.update_one(
                                    {'email': recognized_person, 'group_unique_code': group_code},
                                    {'$addToSet': {'matched_images_uuid': image_uuid}},
                                    upsert=True
                                )
                            else:
                                print(f"No match found for {file_path}")
                    return jsonify(status='success')
                else:
                    return jsonify(status='failure', message='No known embeddings found for this group.')
            else:
                return jsonify(status='failure', message='You are already a member of this group.')
        else:
            return jsonify(status='failure', message='Group not found.')
    else:
        return jsonify(status='failure', message='Invalid group code.')
    
from flask import send_file
@app.route('/download_images', methods=['POST'])
def download_images():
    # Get the JSON string of selected image filenames from the form data
    selected_images_json = request.form.get('selectedImages')

    # Parse the JSON string to a Python list
    selected_images = json.loads(selected_images_json)

    # Create a ZIP file to store the selected images
    zip_filename = 'selected_images.zip'
    with ZipFile(zip_filename, 'w') as zip:
        for filename in selected_images:
            # Get the file path of the selected image
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                # Add the image to the ZIP file
                zip.write(file_path, filename)

    # Send the ZIP file to the client for download
    return send_file(zip_filename, as_attachment=True)
# import shutil
from flask import jsonify, request

@app.route('/delete_images', methods=['POST'])
def delete_images():
    # Get the list of image filenames to be deleted from the request JSON data
    selected_images = request.json.get('images', [])

    if not selected_images:
        return jsonify(status='failure', message='No images selected for deletion.')

    try:
        # Loop through the list of image filenames and delete them from the database
        for image_filename in selected_images:
            # Assuming your collection name is 'images'
            images_collection.delete_one({'filename': image_filename})

            # If the images are stored as files on the server, you can also delete them from the file system
            # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        return jsonify(status='success', message='Selected images deleted successfully.')
    except Exception as e:
        return jsonify(status='failure', message=str(e))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
