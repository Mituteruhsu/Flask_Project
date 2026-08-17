# forms/user_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, Optional

class UserForm(FlaskForm):
    username = StringField("帳號", validators=[DataRequired(), Length(3, 100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    # 編輯時可留空＝不改密碼
    password = PasswordField("密碼", validators=[Optional(), Length(min=6)])
    role_ids = SelectMultipleField("角色", coerce=int, validators=[DataRequired()])