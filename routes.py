from flask import Flask, render_template, redirect, request, session, \
                  flash, url_for 
import os
import time
import datetime                 
import pymongo
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
db = pymongo.Connection("mongodb://localhost").g33k


def mailgun(email, name, type):
    key = os.environ["MAILGUN_KEY"]
    with open('data/welcomemail.txt') as f:
        text = f.read()
        text = text.replace("...type...", type)
        text = text.replace("...name...", name)
    r = requests.post(
            "https://api.mailgun.net/v2/sandboxaafd9ee615e54f49af424db82ccf028a.mailgun.org/messages",
            auth=("api", key),
            data={
                "from": "Alex Mathew <alexmathew003@gmail.com>",
                "to": email,
                "subject": "Welcome to G33K !",
                "text": text
            }
        )
    return


def login_required(f):
    @wraps(f)
    def function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return function


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    session['type'] = 'unknown'
    return render_template('home.html')


@app.route('/learner', methods=['GET', 'POST'])
def learner():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.learners.find_one({ '_id': username })
        if user is not None and user['_id'] == username and user['password'] == hash(password):
            session['username'] = username
            session['type'] = 'learner'
            return redirect('index')
        else:
            flash('Invalid username/password')
            return redirect('learner')          
    return render_template('learner.html')


@app.route('/trainer', methods=['GET', 'POST'])
def trainer():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.trainers.find_one({ '_id': username })
        if user is not None and user['_id'] == username and user['password'] == hash(password):
            session['username'] = username
            session['type'] = 'trainer'
            return redirect('index')
        else:
            flash('Invalid username/password')
            return redirect('trainer')          
    return render_template('trainer.html')


@app.route('/trainer_signup')
def trainer_signup():
    return render_template('trainer_signup.html')


@app.route('/learner_signup')
def learner_signup():
    characters = db.characters.find()
    return render_template('learner_signup.html', characters=characters)


@app.route('/verify_trainersignup', methods=['POST'])
def verify_trainersignup():
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    trainers = db.trainers
    if trainers.find_one({ '_id': username }) is None:
        trainers.insert({
            '_id': username,
            'name': name,
            'email': email,
            'password': hash(password),
            'tutorials': []
            })
        session['username'] = username
        session['type'] = 'trainer'
        mailgun(email, name, 'trainer')
        return redirect('index')
    else:
        flash('The username "%s" is already taken' % (username))
        return redirect('trainer_signup')


@app.route('/verify_learnersignup', methods=['POST'])
def verify_learnersignup():
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    squad = request.form['squad']
    squadname = request.form['squadname']
    resignup = False
    learners = db.learners
    if learners.find_one({ '_id': username }) is not None:
        resignup = True
        flash('The username "%s" is already taken' % (username))
    members = set([person.strip().title() for person in squad.split(',')])
    if len(members) is not 5:
        resignup = True
        flash('You should have exactly 5 members in your squad')
    characters = {result['name'] for result in db.characters.find({}, {'_id': 0, 'name': 1})}
    if len(members - characters) != 0:
        resignup = True
        flash('You should have members only from the list given')
    if resignup:
        return redirect('learner_signup')
    else:
        squadstats = [db.characters.find_one({'name': member}) for member in members]
        learners.insert({
            '_id': username,
            'name': name,
            'email': email,
            'password': hash(password),
            'squadname': squadname,
            'squad': [
                {
                    'name': member['name'],
                    'skills-web': member['skills-web'],
                    'skills-mobile': member['skills-mobile'],
                    'skills-design': member['skills-design'],
                    'skills-databases': member['skills-databases'],
                    'skills-systems': member['skills-systems']
                }
                for member in squadstats
                ]
            })
        session['username'] = username
        session['type'] = 'learner'
        mailgun(email, name, 'learner')
        return redirect('index')


@app.route('/index')
@login_required
def index():
    return render_template(
        'index.html',
        learner=(session['type']=="learner"),
        trainer=(session['type']=="trainer")
        )


@app.route('/trainer/<username>')
def trainerprofile(username):
    person = db.trainers.find_one({ '_id': username })
    if person is None:
        error = True
        details = {'username': username}
    else:
        error = False
        details = {
            'name': person['name'],
            'tutorials': person['tutorials'],
            'tutorialcount': len(person['tutorials'])
        }
    return render_template(
        'trainerprofile.html', 
        error=error, 
        details=details,
        learner=(session['type']=="learner"),
        trainer=(session['type']=="trainer")
        )


@app.route('/learner/<username>')
def learnerprofile(username):
    person = db.learners.find_one({ '_id': username })
    if person is None:
        error = True
        details = {'username': username}
    else:
        error = False
        details = {
            'name': person['name'],
            'squadname': person['squadname'],
            'squad': person['squad']
        }
    return render_template(
        'learnerprofile.html', 
        error=error, 
        details=details,
        learner=(session['type']=="learner"),
        trainer=(session['type']=="trainer")
        )


@app.route('/profile')
@login_required
def profile():
    return redirect(url_for(session['type'] + 'profile', username=session['username']))


@app.route('/search/<type>', methods=['POST'])
def search(type):
    searchterm = request.form['term']
    return redirect(url_for(type + 'profile', username=searchterm))


def generate_permalink(title, today):
    import re
    title = title.strip()
    pattern = re.compile("[^\w ]")
    templink = re.sub(pattern, '', title).replace(" ", "_")
    permalink = "_".join([timestamp, templink])
    return permalink


def convertmdtohtml(content):
    # Thank you StackOverflow !
    import urllib2, json
    data = {'text': content}
    json_data = json.dumps(data)
    req = urllib2.Request("https://api.github.com/markdown")
    result = urllib2.urlopen(req, json_data)
    html = '\n'.join(result.readlines())
    return html


@app.route('/addtutorial', methods=['GET', 'POST'])
@login_required
def addtutorial():
    if request.method != 'POST':
        if session['type'] == "learner":
            return redirect(url_for('index'))
        return render_template(
            'addtutorial.html',
            learner=(session['type']=="learner"),
            trainer=(session['type']=="trainer")
            )
    timestamp = int(time.time())
    author_username = session["username"]
    author_name = db.trainers.find_one({ '_id': author_username })['name']
    category = request.form['category']
    skillincrease = float(request.form['skillincrease'])
    title = request.form['title']
    date = datetime.date.today().ctime()
    permalink = generate_permalink(title, timestamp)
    content = request.form['content']
    html = convertmdtohtml(content)
    html = "{% extends \"tutorial.html\" %}\n{% block content %}\n" + html + "\n{% endblock %}"
    with open('templates/tutorials/' + str(timestamp) + '.html', 'w') as f:
        f.write(html)
    trainer_data = {
        'permalink': permalink,
        'title': title,
        'date': date
        }
    tutorial_data = {
        'timestamp': timestamp,
        'author_name': author_name,
        'author_username': author_username,
        'category': category,
        'skillincrease': skillincrease,
        'title': title,
        'date': date,
        'permalink': permalink
        }
    db.tutorials.insert(tutorial_data)
    db.trainers.update(
        { '_id': author_username },
        { '$push': { 'tutorials': trainer_data } }
        )
    with open('templates/index.html') as f:
        indexpage = f.read()
    print indexpage
    indexpage = indexpage.replace(
        '<h3>G33K Activity</h3>',
        '<h3>G33K Activity</h3>\n<li class="list-group-item"> \
        <a href="/trainer/%s">%s</a> posted a new tutorial - \
        <a href="/%s">%s</a></li>' % (author_username, author_name, permalink, title)
        )
    print indexpage
    with open('templates/index.html', 'w') as f:
        f.write()
    return redirect('index')


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session['type'] = 'unknown'
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
