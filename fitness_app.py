from flask import Flask,request,render_template,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_misaka import Misaka
import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
app=Flask(__name__)
Misaka(app)

db_uri='mysql+pymysql://root:@localhost/fitness?charset=utf8'
app.config['SQLALCHEMY_DATABASE_URI']=db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)

load_dotenv()
openai_api_key=os.getenv('OPENAI_API_KEY')
client=OpenAI()


class Sleep(db.Model):
    __tablename__='sleep'
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    day=db.Column(db.Date,nullable=False)
    sleeptime=db.Column(db.Time,nullable=False)
    getuptime=db.Column(db.Time,nullable=False)
    review=db.Column(db.Text())
class Walk(db.Model):
   __tablename__='walk'
   id=db.Column(db.Integer,primary_key=True,autoincrement=True)
   day=db.Column(db.Date,nullable=False)
   walknum=db.Column(db.Integer,nullable=False)
   review=db.Column(db.Text())

@app.route('/')
def list():
    return render_template('main.html')


@app.route('/sleep')
def sleep():
    db.session.expire_all()
    result=db.session.execute(text("SELECT * FROM sleep"))
    sleeps=result.fetchall()
    return render_template('sleep.html',sleeps=sleeps)
@app.route('/sleep/record')
def sform():

    return render_template('sleep_form.html')
@app.route('/sleep/store',methods=['POST'])
def sstore():
    new_sleep=Sleep()
    new_sleep.day=request.form['day']
    new_sleep.sleeptime=request.form['sleeptime']
    new_sleep.getuptime=request.form['getuptime']
    
    response=client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"あなたはアドバイザーです。これから起床時間と睡眠時間が与えられますので、健康に関するアドバイスをしてください"},
            {"role":"user","content":new_sleep.day+"は、"+new_sleep.sleeptime+"から"+new_sleep.getuptime+"まで寝ました"}
        ],
    )
    review=response.to_dict()
    new_sleep.review=review['choices'][0]['message']['content']
    try:
        
        db.session.add(new_sleep)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error:",e)
    return redirect('/sleep')
@app.route('/sleep/detail/<int:id>')
def sshow(id):
    post=Sleep.query.get(id)

    return render_template('sleep_show.html',post=post)
@app.route('/walk')
def walk():
    db.session.expire_all()
    result=db.session.execute(text("SELECT * FROM walk"))
    walks=result.fetchall()
    data1=[row[1] for row in walks]
    data2=[row[2] for row in walks]
    img=io.BytesIO()
    plt.figure(figsize=(5,4))
    plt.bar(range(len(data1)),data2)
    plt.title('record of walking')
    plt.xlabel('date')
    plt.ylabel('distance')
    plt.xticks(range(len(data1)),data1)
    plt.savefig(img,format='png')
    img.seek(0)
    graph=base64.b64encode(img.getvalue()).decode()
    plt.close()
    return render_template('walk.html',walks=walks,graph=graph)
@app.route('/walk/record')
def wform():
    return render_template('walk_form.html')
@app.route('/walk/store',methods=['POST'])
def wstore():
    new_walk=Walk()
    new_walk.day=request.form['day']
    new_walk.walknum=request.form['walknum']
    response=client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"あなたはアドバイザーです。これから起床時間と睡眠時間が与えられますので、健康に関するアドバイスをしてください"},
            {"role":"user","content":new_walk.day+"は、"+new_walk.walknum+"歩歩きました"}
        ],
    )
    review=response.to_dict()
    new_walk.review=review['choices'][0]['message']['content']
    try:
        db.session.add(new_walk)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error:",e)
    return redirect('/walk')
@app.route('/walk/detail/<int:id>')
def wshow(id):
    post=Walk.query.get(id)

    return render_template('walk_show.html',post=post)
if __name__=='__main__':
    app.run(debug=True)

    