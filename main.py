from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)
   

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    password = db.Column(db.String(50))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')
            

    return render_template('login.html')


@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html',  users=users)

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()

       #TODO add conditionals to authenticate a valid user login

        if not existing_user and len(username) > 3 and len(password) > 3 and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username

            return redirect('/newpost')

        if len(username) == 0:
            flash('Required Field')
        if len(username) < 3:
            flash('Username must be more than 3 characters')

        if len(password) == 0: #only catching this 1.... why!?
            flash('Required Field')
        if len(password) < 3 and len(password) >= 1:
            flash('Must be more than 3 characters')
        if password != verify:
            flash('Passwords do not match')#logs someone in even with just a password

        if username == existing_user:
            flash('Existing User')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/blog', methods=['POST','GET'])
def blog():
   
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')
    posts = Blog.query.order_by(Blog.pub_date.desc())

    if blog_id:
        post = Blog.query.filter_by(id=blog_id).first()
        return render_template("post.html", title=post.title, body=post.body, user=post.owner.username, pub_date=post.pub_date, user_id=post.owner_id)
    if user_id:
        entries = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('user.html', entries=entries)
    return render_template('blog.html', posts=posts)

@app.route('/newpost', methods=['POST','GET'])
def newpost():
    owner = User.query.filter_by(username=session['username']).first()  
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        

        title_error = ''
        body_error = ''
      

        if not title.strip():
            title_error = "Please fill in a title for your blog post"
        if not body.strip():
            body_error = "Please fill in the body of your blog post"
        
        if not title_error and not body_error:
            new_blog = Blog(title, body, owner)
            db.session.add(new_blog)
            db.session.commit()

            return redirect('/blog?id={0}'.format(new_blog.id))
        else:
            return render_template('newpost.html', title=title, body=body, owner=owner, title_error=title_error, body_error=body_error, owner_error=owner_error)
        
    else:
        return render_template('newpost.html')


if __name__ == '__main__':
    app.run()
    