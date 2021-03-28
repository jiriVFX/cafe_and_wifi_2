from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import random
import os
from forms import AddCafeForm

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
# .env file should contain your API_KEY, e.g. API_KEY=YourOwnApiKey
API_KEY = os.environ.get("API_KEY")
# Connect to the Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Cafe Table Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        # Loop through each column in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


# HTTP GET - home
@app.route("/")
def home():
    page = request.args.get("page", default=1, type=int)
    cafes = db.session.query(Cafe).paginate(per_page=10)
    #user_agent = request.headers.get("User-Agent")
    return render_template("cafes.html", cafes=cafes)


# HTTP GET - Get random Cafe
@app.route("/random")
def get_random_cafe():
    cafes = db.session.query(Cafe).all()
    random_cafe = random.choice(cafes).to_dict()

    return jsonify(random_cafe)


# HTTP GET - Get all cafes
@app.route("/all")
def get_all_cafes():
    cafes = db.session.query(Cafe).all()
    cafes_dict = {}
    return jsonify(cafes=[cafe.to_dict() for cafe in cafes])


# HTTP GET - Search by location
@app.route("/search")
def search_cafes():
    location = str(request.args.get("loc"))
    page = request.args.get("page", default=1, type=int)
    cafes = Cafe.query.filter_by(location=location).paginate(per_page=10)
    user_agent = request.headers.get("User-Agent")
    print(user_agent)
    if cafes:
        if user_agent:
            # If it's request coming from a browser
            return render_template("cafes.html", cafes=cafes, location=location)
        else:
            # If it's an API call
            return jsonify(cafes=[cafe.to_dict() for cafe in cafes])
    else:
        if user_agent:
            # If it's request coming from a browser
            return render_template("cafes.html", notfound="Sorry, we couldn't find a cafe at that location. "
                                                          "Try to be more specific or search for different locations.",
                                   location=location)
        else:
            # If it's an API call
            return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})


# HTTP POST - Create new record (cafe)
@app.route("/add", methods=["POST", "GET"])
def add_cafe():
    add_cafe_form = AddCafeForm()
    user_agent = request.headers.get("User-Agent")
    # Remove all previous flash messages
    session.pop('_flashes', None)

    if request.method == 'POST':
        name = request.form["name"]

        # if cafe with entered name is already in database
        if Cafe.query.filter_by(name=name).first():
            flash("Café with this name is already in the database.")
            return render_template("add_cafe.html", form=add_cafe_form)
        else:
            # Convert checkbox default values of "y" and None into boolean values
            # If request was made through API, values will be "1" or "0"
            if request.form.get("has_toilet") == "y" or request.form.get("has_toilet") == "1":
                has_toilet = True
            else:
                has_toilet = False
            if request.form.get("has_wifi") == "y" or request.form.get("has_wifi") == "1":
                has_wifi = True
            else:
                has_wifi = False
            if request.form.get("has_sockets") == "y" or request.form.get("has_sockets") == "1":
                has_sockets = True
            else:
                has_sockets = False
            if request.form.get("can_take_calls") == "y" or request.form.get("has_sockets") == "1":
                can_take_calls = True
            else:
                can_take_calls = False

            new_cafe = Cafe(
                name=name,
                map_url=request.form["map_url"],
                img_url=request.form["img_url"],
                location=request.form["location"],
                seats=request.form["seats"],
                has_toilet=has_toilet,
                has_wifi=has_wifi,
                has_sockets=has_sockets,
                can_take_calls=can_take_calls,
                coffee_price=str(request.form["coffee_price"])
            )
            # Add the new cafe to the database
            db.session.add(new_cafe)
            # Commit the changes
            db.session.commit()
        if user_agent:
            flash("Café successfully added to the database.")
            # Flash messages don't work on redirect, so we don't redirect, but empty the form
            add_cafe_form.name.data = ""
            add_cafe_form.map_url.data = ""
            add_cafe_form.img_url.data = ""
            add_cafe_form.location.data = ""
            add_cafe_form.seats.data = ""
            add_cafe_form.has_toilet.data = None
            add_cafe_form.has_wifi.data = None
            add_cafe_form.has_sockets.data = None
            add_cafe_form.can_take_calls.data = None
            add_cafe_form.coffee_price.data = None
            return render_template("add_cafe.html", form=add_cafe_form)
        else:
            return jsonify(response={"success": "Successfully added the new cafe."})
    else:
        return render_template("add_cafe.html", form=add_cafe_form)


# HTTP PUT/PATCH - Update record (cafe)
@app.route("/update-price/<int:cafe_id>", methods=["GET", "PATCH"])
def update_price(cafe_id):
    new_price = request.args.get("new_price")
    cafe_to_update = Cafe.query.get(cafe_id)
    # If cafe was found in the database
    if cafe_to_update:
        cafe_to_update.coffee_price = new_price
        db.session.commit()
        # Success 200
        return jsonify(response={"success": f"Successfully updated coffee price to {new_price}."}), 200
    else:
        # Not Found 404
        return jsonify(response={"Not Found": "Sorry, a cafe with that id was not found in the database."}), 404


# HTTP DELETE - Delete Record (remove cafe)
@app.route("/remove-cafe/<int:cafe_id>", methods=["GET", "DELETE"])
def delete_cafe(cafe_id):
    secret_key = request.args.get("api-key")
    cafe_to_delete = Cafe.query.get(cafe_id)
    # If correct Api key is provided
    if secret_key == API_KEY:
        # If cafe was found in the database
        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            # Success 200
            return jsonify(response={"Success": "Successfully removed the cafe from the database."}), 200
        else:
            # Not Found 404
            return jsonify(response={"Not Found": "Sorry, a cafe with that id was not found in the database."}), 404
    else:
        # Forbidden 403
        return jsonify(response={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api-key"}), 403


if __name__ == '__main__':
    app.run(debug=True)
