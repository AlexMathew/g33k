import os
import json
import random
import requests
import pymongo


def genderize(name):
	r = requests.get(
			"https://genderize.p.mashape.com/?country_id=US&language_id=en&name=%s" % (name), 
			headers={"X-Mashape-Key": os.environ['MASHAPEKEY']}
			)
	gender = r.json()['gender']
	return gender if gender in ['male', 'female'] else 'male'


def load_data():
	with open('data/judges.json') as f:
		judges = json.load(f)
	return judges


def set_data(judges):
	names = [name.split(' ')[0] for name in judges.keys()]
	hackers = []
	for name in names:
		hacker = {
			'name': name,
			'gender': genderize(name),
			'skills-web': round(random.random()/0.33, 1),
			'skills-mobile': round(random.random()/0.33, 1),
			'skills-design': round(random.random()/0.33, 1),
			'skills-databases': round(random.random()/0.33, 1),
			'skills-systems': round(random.random()/0.33, 1)
		}
		hackers.append(hacker)
	updateDB(hackers)


def updateDB(data):
	connection = pymongo.Connection("mongodb://localhost")
	db = connection.g33k
	characters = db.characters
	for character in data:
		characters.update(
			{ 'name': character['name'] }, 
			{ '$set': character },
			upsert=True
			)
	return


if __name__ == '__main__':
	judges = load_data()
	set_data(judges)