from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, URL


# WTForm
class AddCafeForm(FlaskForm):
    name = StringField("Café name", validators=[DataRequired()])
    map_url = StringField("Google Maps URL", validators=[DataRequired(), URL()])
    img_url = StringField("Café Image URL", validators=[DataRequired(), URL()])
    location = StringField("Location", validators=[DataRequired()])
    seats = StringField("Number of seats", validators=[DataRequired()])
    coffee_price = StringField("Coffee price", validators=[DataRequired()])
    has_sockets = BooleanField("Power sockets")
    has_toilet = BooleanField("Toilet")
    has_wifi = BooleanField("Stable Wi-Fi")
    can_take_calls = BooleanField("Quiet to take calls")
    submit = SubmitField("Add Café")
