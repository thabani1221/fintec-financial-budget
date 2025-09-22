from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

def load_model():
    import pickle
    import os

    model_path = os.path.join(os.path.dirname(__file__), 'your_model.pkl')
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model