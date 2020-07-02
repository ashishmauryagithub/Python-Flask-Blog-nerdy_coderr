from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os,math

from flask_mail import Mail
from werkzeug.utils import secure_filename

local_server = True

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key='mysecretkey123'
app.config['UPLOAD_FOLDER'] = params['upload_location']






app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = params['gmail_user']
app.config['MAIL_PASSWORD'] = params['gmail_pass']
app.config['MAIL_DEFAULT_SENDER'] = None
app.config['MAIL_MAX_EMAILS'] = None
# app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False
mail = Mail(app)




# app.config.update(
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT=465,
#     MAIL_USE_SSL=True,
#
#     MAIL_USERNAME=params['gmail_user'],
#     MAIL_PASSWORD=params['gmail_pass']
# )

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    phone_num = db.Column(db.String(12), unique=True, nullable=False)
    mes = db.Column(db.String(12), unique=True, nullable=False)
    date = db.Column(db.String(12), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), unique=False, nullable=False)
    tagline = db.Column(db.String(20), unique=False, nullable=False)
    slug = db.Column(db.String(25), unique=True, nullable=False)
    content = db.Column(db.String(120), unique=True, nullable=False)
    img_file = db.Column(db.String(12), unique=True, nullable=False)
    date = db.Column(db.String(12), unique=False, nullable=False)


@app.route('/')
# @app.route('/home')
def home():

    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_post']))
    # [0:params['no_post']]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts = posts[(page-1)*int(params['no_post']):(page-1)*int(params['no_post'])+int(params['no_post'])]

    # pagination logic
    # first
    if(page==1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page==last):
        next = "#"
        prev = "/?page="+str(page-1)
    else:
        next = "/?page="+str(page+1)
        prev = "/?page="+str(page-1)

    # middle

    # prev = page-1
    # next = page +1
    # last
    # next = #
    # prev = page-1










    return render_template('index.html', params=params, posts = posts,prev=prev,next=next)


@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if ('user_session' in session and session['user_session'] == params['admin_user']):
        if request.method == 'POST':

            box_title = request.form.get('title')
            tagline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno == '0':
                post = Posts(title=box_title,tagline=tagline,slug=slug, content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)


@app.route('/dashboard',methods=['GET','POST'])
def dashboard():

    if ('user_session' in session and session['user_session'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method == 'POST':
        username = request.form.get('email')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']  ):
            session['user_session'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)






    return render_template('adminLogin.html', params=params)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user_session' in session and session['user_session'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return redirect('/dashboard')



@app.route('/logout')
def logout():
    session.pop('user_session')
    return redirect('/dashboard')

@app.route('/delete/<string:sno>')
def delete(sno):
    if 'user_session' in session and session['user_session'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # (`sno`, `name`, `phone_num`, `mes`, `date`, `email`)
    #  Add entry to the database

    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        # name = request.get('name')
        entry = Contacts(name=name, email=email, phone_num=phone, mes=message, date=datetime.now())
        db.session.add(entry)

        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone
                          )

    return render_template('contact.html', params=params)


@app.route('/post/<string:slug_name>', methods=['GET'])
def post_route(slug_name):
    post = Posts.query.filter_by(slug=slug_name).first()

    return render_template('post.html', params=params, post=post)


app.run(debug="True")
