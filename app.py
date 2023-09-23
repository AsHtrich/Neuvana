from flask import Flask, render_template, request, url_for, session, send_file, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import requests
from textblob import TextBlob
from bs4 import BeautifulSoup
import re
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time

load_dotenv()
hf_api_key = os.getenv('HF_API_KEY')
Model_URL = os.getenv('Model_URL')
password = os.getenv('password')
mailID = os.getenv('mailID')

app = Flask(__name__,template_folder='templates')
app.secret_key = os.getenv('NeuH_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SDU')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

scheduler = BackgroundScheduler()
scheduler.start()

FILTER = ['harm','harrassment','emotion','stress','mental health','stalking','illness']
FILTER = set(FILTER)
gDate = None
ALink = []
ATitle = []
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

def PUSH_NOTIFICATION():
    global mailID
    global password
    QRY = Users.query.all()
    for qry in QRY:
        user = qry.username
        perf = ConversationScore.query.filter_by(username=user)
        res = perf.all()
        mood = None
        opinions = None
        if len(res) == 0:
            mood = "Calm"
            opinions = "Moderately opinionated"
        else:
            m = 0
            o = 0
            for r in res:
                m += r.polarity
                o += r.subjectivity
            m /= len(res)
            o /= len(res)
            if m < -0.6:
                mood = "Stressed"
            elif m < -0.2:
                mood = "Sad"
            elif m < 0.2:
                mood = "Calm"
            elif m < 0.6:
                mood = "Good"
            else:
                mood = "Great"
            if o < -0.5:
                opinions = "Weakly Opinionated"
            elif o < 0.5:
                opinions = "Moderately Opinionated"
            else:
                opinions = "Strongly Opinionated"
        sender_email = mailID
        receiver_email = qry.email
        password = password
        subject = "Subject: Neuvana Regular Checkup"
        message = "Hello! I hope you are having a lovely day, You seem to be feeling " + mood + " and " + opinions + " today. We hope you are always becoming a better version of yourself nevertheless of where you are in life! See ya soon at Neuvana!"
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)

scheduler.add_job(PUSH_NOTIFICATION, 'interval', minutes=1440)

def LLM_promptFILTER(prompt):
    url = "https://www.google.com/search?q=" + prompt
    response = requests.get(url)
    global FILTER
    if response.status_code == 200:
        data = response.text
        data = str(data)
        if any(word in data for word in FILTER):
            return True
        else:
            return False
    else:
        return False

def query(url,header,send):
    response = requests.post(url, headers=header, json=send)
    return response.json()

def LLMChatBOT_reply(prompt):
    global Model_URL
    global hf_api_key
    prompt = prompt + ". tell me what to do."
    header = {'Authorization': "Bearer " + hf_api_key}
    op = query(Model_URL,header,{"inputs" : prompt})
    reply = op[0]['generated_text']
    Rate_Limit = 9
    while(reply[len(reply)-1] != '.' and Rate_Limit != 0):
        op = query(Model_URL,header,{"inputs": reply})
        reply = op[0]['generated_text']
        Rate_Limit -= 1
    reply = reply[len(prompt):]
    return reply

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

@app.route("/articles")
def articles():
    if 'username' not in session:
        return redirect(url_for('login'))
    global gDate
    global ALink
    global ATitle
    if gDate == date.today():
        return render_template('articles.html',Title = ATitle,Link = ALink,username = session['username'])
    gDate = date.today()
    ALink = []
    ATitle = []
    Link = []
    Title = []
    page = requests.get("https://www.calmsage.com/")
    soup = BeautifulSoup(page.content, 'html.parser')
    res = soup.find_all('a',class_="btn_read")
    for i in range(0,len(res)):
        title = res[i]['href']
        Link.append(title)
        title = re.sub(r'https://www.calmsage.com/','',title)
        title = re.sub(r'-',' ',title)
        title = re.sub(r'/','',title)
        Title.append(title)
    page = requests.get("https://www.health.harvard.edu/blog")
    soup = BeautifulSoup(page.content, 'html.parser')
    res = soup.find_all('a',class_="hover:text-red transition-colors duration-200")
    for i in range(0,len(res)):
        Link.append(res[i]['href'])
        Title.append(res[i].text)
    need = 8
    random.seed(time.time())
    try:
        while(need != 0):
            i = random.randint(0,len(Link))
            ALink.append(Link[i])
            ATitle.append(Title[i])
            Link.pop(i)
            Title.pop(i)
            need -= 1
    except:
        pass

    return render_template('articles.html',Title = ATitle,Link = ALink,username = session['username'])

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    squery = ConversationScore.query.filter_by(username=username)
    scores = squery.all()
    if len(scores) == 0:
        pdata = [0,0,100,0,0]
        x = [0]
        y = [0]
        return render_template('dashboard.html',pdata=pdata,x=x,y=y)
    x = []
    y = []
    emotional_score = [0,0,0,0,0]
    for i in range(0,len(scores)):
        if scores[i].polarity < -0.6:
            emotional_score[0] += 1
        elif scores[i].polarity < -0.2:
            emotional_score[1] += 1
        elif scores[i].polarity < 0.2:
            emotional_score[2] += 1
        elif scores[i].polarity < 0.6:
            emotional_score[3] += 1
        else:
            emotional_score[4] += 1
        x.append(i+1)
        y.append(scores[i].subjectivity)
    pdata = [((emotional_score[i]*100)/len(scores)) for i in range(0,5)]
    return render_template('dashboard.html',username=username,pdata=pdata,x=x,y=y)

@app.route('/chatbot',methods=['GET','POST'])
def chatbot():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        prompt = request.form['prompt']
        prompt = str(prompt)
        reply = None
        if LLM_promptFILTER(prompt) == True:
            polarity = TextBlob(prompt).sentiment.polarity
            subjectivity = TextBlob(prompt).sentiment.subjectivity
            try:
                with app.app_context():
                    newConv = ConversationScore(username=username,polarity=polarity,subjectivity=subjectivity)
                    db.session.add(newConv)
                    db.session.commit()
            except:
                pass
            reply = LLMChatBOT_reply(prompt)
        else:
            reply = 'I am sorry I can not help you with that as I am a Mental-health chatbot'
        render_template('chatbot.html',username=username,reply=reply)
    return render_template('chatbot.html',username=username,reply='Hello '+username+"! How may I help you?")

@app.route('/static/<filename>')
def static_file(filename):
    return send_file(f'static/{filename}')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__=="__main__":
    app.run(debug=True)