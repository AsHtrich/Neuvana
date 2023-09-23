from flask import Flask, render_template, request, url_for, session, send_file, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
hf_api_key = os.getenv('HF_API_KEY')

app = Flask(__name__,template_folder='templates')
app.secret_key = os.getenv('NeuH_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SDU')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(100), nullable = False)
    def __repr__(self) -> str:
        return f"Users(username={self.username}, password={self.password}, email={self.email})"
class ConversationScore(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable = False)
    polarity = db.Column(db.Float, nullable = False)
    subjectivity = db.Column(db.Float, nullable = False)
    def __repr__(self) -> str:
        return f"ConversationScore(username={self.username}, polarity={self.polarity}, subjectivity={self.subjectivity})"

class Stories(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable = False)
    story = db.Column(db.String(1500), nullable = False)
    def __repr__(self) -> str:
        return f"Stories(username={self.username}, story={self.story})"

class TherapyForm(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable = False)
    date = db.Column(db.String(100), nullable = False)
    time = db.Column(db.String(30), nullable = False)
    city = db.Column(db.String(30), nullable = False)
    typeOT = db.Column(db.String(30), nullable = False)
    gender = db.Column(db.String(10), nullable = False)
    ph_no = db.Column(db.String(20), nullable = False)
    def __repr__(self) -> str:
        return f"TherapyForm(username={self.username}, date={self.date}, time={self.time}, city={self.city}, typeOT={self.typeOT}, gender={self.gender}, ph_no={self.ph_no})"
    
with app.app_context():
    db.create_all()

@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        email = str(email)
        password = str(password)
        try:
            with app.app_context():
                log = Users.query.filter_by(email=email,password=password)
                log_check = log.all()
                if len(log_check) == 0:
                    return render_template('login.html',error='Invalid Credentials')
                else:
                    session['username'] = log_check[0].username
                    session['email'] = log_check[0].email
                    return redirect(url_for('dashboard'))
        except:
            return render_template('login.html',error='Server error, we will get back to you shortly')
    return render_template('login.html',error=None)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        username = str(username)
        email = str(email)
        password = str(password)
        with app.app_context():
            try:
                check = Users.query.filter_by(username=username)
                fcheck = check.all()
                if len(fcheck) == 0:
                    try:
                        newuser = Users(username=username,email=email,password=password)
                        db.session.add(newuser)
                        db.session.commit()
                        return render_template('register.html',error='Successfully registered!')
                    except:
                        return render_template('register.html',error='Server error, try again later')
                else:
                    return render_template('register.html',error='User already exists')
            except:
                return render_template('register.html',error='Server error, try again later')
    return render_template('register.html',error = None)


@app.route('/static/<filename>')
def static_file(filename):
    return send_file(f'static/{filename}')

if __name__=="__main__":
    app.run(debug=True)