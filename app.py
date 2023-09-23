from flask import Flask, render_template, request, url_for, session, send_file, redirect
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__,template_folder='templates')

@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        username = str(username)
        password = str(password)
        try:
            with app.app_context():
                log = Users.query.filter_by(username=username,password=password)
                log_check = log.all()
                if len(log_check) == 0:
                    return render_template('login.html',error='Invalid Credentials')
                else:
                    session['username'] = username
                    return redirect(url_for('dashboard'))
        except:
            return render_template('login.html',error='Server error, we will get back to you shortly')
    return render_template('login.html',error=None)

if __name__=="__main__":
    app.run(debug=True)