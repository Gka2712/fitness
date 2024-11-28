from flask import Flask,request,render_template,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_misaka import Misaka
import os
from openai import OpenAI
from dotenv import load_dotenv
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
    print(review['choices'][0]['message']['content'])
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
if __name__=='__main__':
    app.run(debug=True)

    