import os
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app=Flask(__name__)

DATABASE_URL=os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI']=DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)

class Users(db.model):
    userid=db.column(db.Integer,primary_Key=True)




@app.route('/')
def retString():
    return "Hello"

if __name__=="__main__":
    app.run(debug=True)
