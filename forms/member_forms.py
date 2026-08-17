# forms/member_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length

class FamilyMemberForm(FlaskForm):
    nickname = StringField("暱稱", validators=[DataRequired(), Length(1, 50)])
    family_role = SelectField(
        "身份",
        choices=[("parent", "家長"), ("child", "小孩"), ("viewer", "唯讀家人")],
        validators=[DataRequired()],
    )
    is_active = BooleanField("啟用中", default=True)