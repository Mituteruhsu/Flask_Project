# forms/family_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class FamilyForm(FlaskForm):
    name = StringField("家庭名稱", validators=[DataRequired(), Length(1, 100)])
    plan_id = SelectField("訂閱方案", coerce=int, validators=[Optional()])