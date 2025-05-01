from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User
from user import create_user, authenticate, get_user
from vocabulary_service import VocabularyService

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.secret_key = 'secret'

# Initialize the database with the app
db.init_app(app)

# make sure tables exist once
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/vocab')
def vocab():
    return render_template('vocab.html')

@app.route('/vocab/<category>')
def vocabulary_category(category):
    vocab_service = VocabularyService()
    words = vocab_service.get_category_words(category)
    return render_template('vocabulary_category.html', category=category, words=words)

@app.route('/study')
def study_session():
    category = request.args.get('category')
    word_count = int(request.args.get('word_count', 5))
    
    vocab_service = VocabularyService()
    words = vocab_service.generate_study_session(category, word_count)
    
    return render_template('study_session.html', 
                         words=words,
                         category=category,
                         word_count=word_count)

@app.route('/api/random_words')
def api_random_words():
    category = request.args.get('category')
    word_count = int(request.args.get('word_count', 10))
    vocab_service = VocabularyService()
    words = vocab_service.generate_study_session(category, word_count)
    return jsonify({'words': words})

# ---------- register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = create_user(request.form['username'],
                           request.form['email'],
                           request.form['password'])
        if user:
            flash('Registered! Please log in.')
            return redirect(url_for('login'))
        flash('Username or email already exists.')
    return render_template('register.html')

# ---------- login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = authenticate(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user.id
            flash('Logged in!')
            return redirect(url_for('home'))
        flash('Invalid credentials.')
    return render_template('login.html')

# ---------- logout ----------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
