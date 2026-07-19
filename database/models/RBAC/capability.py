from core.database import db

class Capability(db.Model):
    __tablename__ = 'capabilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Capability {self.name}>"