import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

users = mongo.db.users.find()

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html", users=users)

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        existing_email = mongo.db.users.find_one(
                    {"email": request.form.get("email").lower()})
        existing_username = mongo.db.users.find_one(
                        {"username": request.form.get("username").lower()})

        if existing_email:
            flash("Email is already registered.")
            return redirect(url_for('register'))

        if existing_username:
            flash("Username is already in use, please choose a different one.")
            return redirect(url_for('register'))

        password1 = request.form.get("password")
        password2 = request.form.get("password-confirmation")

        if password1 != password2:
            flash("Passwords do not match, please try again.")
            return redirect(url_for('register'))

        register_user = {
        "username": request.form.get("username").lower(),
        "email": request.form.get("email").lower(),
        "password": generate_password_hash(request.form.get("password")),
        "points": None
        }

        mongo.db.users.insert_one(register_user)

        session["user"] = request.form.get("username").lower()
        flash("Registration successful Welcome to the pub quiz!")
        username = session["user"]

    return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        if session:
            if 'user' in session:
                flash("You are already logged in.")
                return redirect(url_for('home'))

            else:
                return render_template("login.html")
        else:
            return render_template("login.html")

    if request.method == "POST":
        email = request.form.get("email").lower()
        password = request.form.get("password")

        existing_user = mongo.db.users.find_one(
        {"email": email})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], password):
                username = existing_user["username"]
                session["user"] = username
                flash(f"Welcome, {username}!")
                return redirect(url_for("home"))
            else:
                flash("Incorrect username and/or password!")
                return redirect(url_for("login"))
        else:
            flash("Incorrect username and/or password!")
            return redirect(url_for("login"))


@app.route("/logout")
def logout():

    if session:
        if 'user' in session:

            session.pop("user", None)
            flash("You've been logged out")
            return redirect(url_for("login"))

        else:
            flash("You're not logged in.")
            return redirect(url_for("login"))
    else:
        flash("You're not logged in.")
        return redirect(url_for("login"))


def rand_num():
    return randint(00000, 99999)


@app.route("/create_battle", methods=["GET", "POST"])
def create_battle():

    if request.method == "POST":
        if session:
            if "user" in session:
                username = session["user"]
                user = mongo.db.users.find_one({"username": username})
                user_id = user["_id"]

                #need a way to make sure that the battle pin has not been generated already.
                # While existing battle pin run the function?  


                existing_battle = mongo.db.battles.find_one(
                            {"battle_name": request.form.get("battle_name").lower()})

                if existing_battle:
                    flash("That Battle Name is Taken, please choose a different one.")
                    return redirect(url_for('create_battle'))

                battle_pin = rand_num()
                existing_battle_pin = mongo.db.battles.find_one({"battle_pin": battle_pin})

                while existing_battle_pin != None:
                    battle_pin = rand_num()
                    existing_battle_pin = mongo.db.battles.find_one({"battle_pin": battle_pin})

                battle_name = request.form.get("battle_name").lower()

                register_battle = {
                "battle_name": battle_name,
                "players": [user_id],
                "battle_pin": battle_pin,
                "scores": []
                }

                mongo.db.battles.insert_one(register_battle)

                flash(f"Your {battle_name} battle has been created! Welcome to the quiz! Your battle pin is {battle_pin}, share this with your competitors to battle it out!")
                username = session["user"]
                return redirect(url_for('battleground', battle_pin=battle_pin))

    return render_template("create_battle.html")


@app.route("/join-battle", methods=["GET", "POST"])
def join_battle():

    if session:
        if 'user' in session:

            if request.method == "POST":
                inserted_pin = int(request.form.get("pin"))

                battle = mongo.db.battles.find_one({"battle_pin": inserted_pin})

                if battle is not None:

                    user_name = session["user"]
                    user = mongo.db.users.find_one({"username": user_name})

                    # adds player username to battle's players array
                    mongo.db.battles.update_one({"battle_pin": inserted_pin},
                                                 {'$push': {"players": user["_id"]}})


                    return redirect(url_for('battleground', battle_pin=inserted_pin, username=user_name))

                else:
                    flash("Sorry, but that battle pin is incorrect. Please try again.")
                    return render_template("join-battle.html")

            return render_template("join-battle.html")

        else:
            flash("You need to be logged in to join a quiz battle!")
            return redirect(url_for('login'))
    else:
        flash("You need to be logged in to join a quiz battle!")
        return redirect(url_for('login'))



@app.route("/battleground/<battle_pin>/<username>")
def battleground(battle_pin, username):

    if request.method == "POST":
        # player_score = request.form.get("score")

        player_score = "23"

        # Add this player score into the array of battle_scores

        mongo.db.battles.update_one({"battle_pin": int(battle_pin)},
                                    {'$push':
                                    {"battle_scores":
                                     [username, int(player_score)]}})

        battle_scores = battle["battle_scores"]

        print(battle_scores)

        # Send the updated battle_pin to the leaderboard for display
        # the battle pin will contain the updated scores via the battle obj.

        return redirect(url_for('leaderboard', battle_pin=battle_pin))

    battle = mongo.db.battles.find_one({"battle_pin": int(battle_pin)})
    battle_name = battle["battle_name"]
    player = mongo.db.users.find_one({"username":username})

    return render_template("battleground.html",
                           battle_pin=battle_pin,
                           battle_name=battle_name,
                           player=player, battle=battle)


@app.route("/leaderboard/<battle_pin>")
def leaderboard(battle_pin):

    # use the battle pin to return the correct battle for score display

    # find the updated battle scores array and sanitize it for displaying. 



    return render_template('leaderboard.html', battle=battle, battle_scores=battle_scores)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
    port=int(os.environ.get("PORT")),
    debug=True)
