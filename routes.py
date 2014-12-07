from flask import Flask, render_template, redirect, request, session, escape, url_for, \
				  flash
import os				  
import pymongo

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
db = pymongo.Connection("mongodb://localhost").g33k


@app.route('/')
def home():
	if 'username' in session:
		return render_template('index.html')
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
	email = request.form['email']
	password = request.form['password']
	trainers = db.trainers
	if trainers.find_one({ '_id': username }) is None:
		trainers.insert({
			'_id': username,
			'email': email,
			'password': hash(password)
			})
		session['username'] = username
		session['type'] = 'trainer'
		return redirect('index')
	else:
		flash('The username "%s" is already taken' % (username))
		return redirect('trainer_signup')


@app.route('/verify_learnersignup', methods=['POST'])
def verify_learnersignup():
	username = request.form['username']
	email = request.form['email']
	password = request.form['password']
	squad = request.form['squad']
	squadname = request.form['squadname']
	resignup = False
	learners = db.learners
	if learners.find_one({ '_id': username }) is not None:
		resignup = True
		flash('The username "%s" is already taken' % (username))
	members = set([name.strip().title() for name in squad.split(',')])
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
		return redirect('index')


@app.route('/index')
def index():
	return render_template(
		'index.html',
		learner=(session['type']=="learner"),
		trainer=(session['type']=="trainer")
		)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session['type'] = 'unknown'
    return redirect(url_for('home'))


if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8000, debug=True)
