from flask import Flask, render_template, redirect, request, session, escape, url_for
import pymongo

app = Flask(__name__)


@app.route('/')
def home():
	return render_template('home.html')


@app.route('/learner')
def learner():
	return render_template('learner.html')


@app.route('/trainer')
def trainer():
	return render_template('trainer.html')


@app.route('/trainer_signup')
def trainer_signup():
	return render_template('trainer_signup.html')


@app.route('/learner_signup')
def learner_signup():
	return render_template('learner_signup.html')


@app.route('/authenticate_trainer')
def auth_trainer():
	return render_template('profile.html')


@app.route('/authenticate_learner')
def auth_learner():
	return render_template('profile.html')


if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8000, debug=True)
