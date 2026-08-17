# forms/invoice_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

class InvoiceForm(FlaskForm):
    invoice_num = StringField("發票號碼", validators=[DataRequired(), Length(1, 50)])
    invoice_date = StringField("開立日期", validators=[Optional(), Length(0, 20)])
    total_amount = StringField("總金額", validators=[Optional(), Length(0, 50)])
    buyer_invoice_num = StringField("買方統編", validators=[Optional(), Length(0, 20)])
    seller_invoice_num = StringField("賣方統編", validators=[Optional(), Length(0, 20)])
    items_detail = TextAreaField("品項明細", validators=[Optional()])