import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email details
sender_email = "bandarohan65@gmail.com"
receiver_email = "rohanbanda103@gmail.com"
subject = "Subject of the Email"
body = "Body of the Email"

# Create a MIME object
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject

# Attach body to the email
message.attach(MIMEText(body, "plain"))

# Establish a connection with the SMTP server
smtp_server = "smtp.gmail.com"  # Replace this with your SMTP server
smtp_port = 587  # Replace with your SMTP port
username = "bandarohan65@gmail.com"  # Replace with your username
password = "nilp tyqs qjdv rwrp"  # Replace with your password

# Start TLS encryption
server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()

# Login to your account
server.login(username, password)

# Send email
server.sendmail(sender_email, receiver_email, message.as_string())

# Quit SMTP server
server.quit()



# def generate_otp():
#     return str(randint(1000, 9999))

# def send_otp_email(email, otp):
#     msg = Message('Password Reset OTP', recipients=[email])
#     msg.body = f'Your OTP for password reset is: {otp}'
#     mail.send(msg)

# # Route for sending OTP email
# @app.route('/forgot_password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'POST':
#         email = request.form['email']
#         user = users_collection.find_one({'email': email})
#         if user:
#             # Generate OTP
#             otp = generate_otp()
#             # Save the OTP in the database or associate it with the user's record
#             users_collection.update_one({'email': email}, {'$set': {'reset_otp': otp}})
#             # Send OTP to user's email
#             send_otp_email(email, otp)
#             flash('An OTP has been sent to your email. Please check your inbox.', 'success')
#             return redirect(url_for('verify_otp'))
#         else:
#             flash('Email address not found.', 'error')
#     return render_template('forgot_password.html')

# @app.route('/verify_otp', methods=['GET', 'POST'])
# def verify_otp():
#     if request.method == 'POST':
#         otp_entered = request.form['otp']
#         email = request.form['email']
#         user = users_collection.find_one({'email': email})
#         if user and 'reset_otp' in user and user['reset_otp'] == otp_entered:
#             # Valid OTP, allow password reset
#             return redirect(url_for('reset_password', email=email))
#         else:
#             flash('Invalid OTP. Please try again.', 'error')
#     return render_template('verify_otp.html')


# # Update the reset_password route to include email parameter
# @app.route('/reset_password', methods=['GET', 'POST'])
# def reset_password():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         confirm_password = request.form['confirm_password']
#         if password == confirm_password:
#             # Update the password in the database
#             hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#             users_collection.update_one({'email': email}, {'$set': {'password': hashed_password, 'reset_otp': None}})
#             flash('Password reset successfully. You can now login with your new password.', 'success')
#             return redirect(url_for('login'))
#         else:
#             flash('Passwords do not match.', 'error')
#     return render_template('reset_password.html')

