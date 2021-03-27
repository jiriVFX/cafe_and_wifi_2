from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import random
import os
from forms import AddCafeForm
from distutils.util import strtobool

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
    return render_template("cafes.html")


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
    cafes = Cafe.query.filter_by(location=location).all()
    user_agent = request.headers.get("User-Agent")
    print(user_agent)
    if cafes:
        if user_agent:
            # If it's request coming from a browser
            return render_template("cafes.html", cafes=[cafe.to_dict() for cafe in cafes], location=location)
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

    if request.method == 'POST':
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
            name=request.form["name"],
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
            return render_template("add_cafe.html", form=add_cafe_form, success="Café successfully added!")
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
