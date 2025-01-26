from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, make_response
import os
import mysql.connector
from dotenv import load_dotenv
import google.generativeai as genai
from werkzeug.security import generate_password_hash, check_password_hash
from xhtml2pdf import pisa
from io import BytesIO



# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]  # Set your secret key for session management

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.environ["DB_PASSWORD"]
app.config['MYSQL_DB'] = os.environ["DB_NAME"]

# Connect to MySQL
db = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

# Configure the Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model with your desired configurations
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 512,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Serve the welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Serve the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

# Serve the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
    
    return render_template('register.html')

# Serve the index page
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    data = request.get_json()
    topic = data.get('topic')
    num_questions = data.get('num_questions', 5)

    # Create the chat session for generating questions
    chat_session = model.start_chat(history=[
        {
            "role": "user",
            "parts": [f"Generate {num_questions} questions about {topic}."]
        }
    ])

    response = chat_session.send_message("INSERT_INPUT_HERE")

    # Extract questions from the response
    questions = response.text.strip().split('\n')

    return jsonify({"questions": questions})

 # Route to generate the PDF
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    topic = data.get('topic')
    questions = data.get('questions', [])

    # Render the HTML template for the PDF
    rendered_html = render_template(
        'pdf_template.html',  # This is the template for the PDF
        topic=topic,
        questions=questions,
        enumerate=enumerate  # Allows numbering in the template
    )

    # Create the PDF
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(rendered_html.encode('utf-8')), dest=pdf)

    if pisa_status.err:
        return jsonify({"error": "Error generating PDF"}), 500

    # Send the PDF as a response
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={topic}_questions.pdf'
    
    return response



if __name__ == '__main__':
    app.run(debug=True)
