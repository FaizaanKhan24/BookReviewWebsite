import os
import requests
from Properties import BookData
from flask import Flask,session,render_template,request,redirect,url_for,jsonify,abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

app = Flask(__name__)
app.secret_key='ChamberOfSecrets'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure system to use filesystem
app.config["SESSION_PERMANENT"]=False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# # Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# App routes
@app.route("/",methods=['POST','GET'])
def index():
    if request.method=='POST':
        session.pop('username',None)
        username = request.form['username']
        password = request.form['password']
        userDetails = db.execute("SELECT * FROM logindata WHERE username = :username",{"username":username}).fetchone()
        if userDetails is None:
            return render_template("Error.html",Message="No such user exist. Enter a valid username and password")
        else:
            if userDetails.password == password:
                session['username']=username
                return redirect(url_for('search',username=username))
            else:
                return render_template("home.html")
    return render_template("home.html")

@app.route("/register", methods=['POST','GET'])
def addUser():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        if username is "" or password is "":
            return render_template("Error.html",Message="Fields cannot be empty")
        db.execute("INSERT INTO logindata(username,password) VALUES (:username , :password)",{"username":username,"password":password})
        db.commit()
        return render_template("Success.html")
    return render_template("Register.html")

@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))

@app.route("/<string:username>/search",methods=['POST','GET'])
def search(username):
    if request.method=='POST':
        searchValue = request.form['search']
        if not searchValue:
            return render_template("Search.html",username=username)
        return redirect(url_for('mainPage',searchValue=searchValue,username=username))
    return render_template("Search.html",username=username)

@app.route("/<string:username>/main/<string:searchValue>")
def mainPage(username,searchValue):
    searchValue = '%'+searchValue+'%'
    bookdetails = db.execute("SELECT * FROM bookdetails WHERE isbn LIKE :searchValue OR title LIKE :searchValue OR author LIKE :searchValue ",{"searchValue":searchValue}).fetchall()
    if len(bookdetails)==0:
        return render_template("Error.html",Message="No such records exist.")
    return render_template("Main.html",bookdetails=bookdetails,username=username)

@app.route("/<string:username>/book/<string:book_isbn>",methods=['POST','GET'])
def bookData(book_isbn,username):

    if request.method=='POST':
        ratingValue = request.form['review_number']
        userReview = request.form['book_review']
        reviewData = book_isbn + '&&' + username + '&&' + str(ratingValue) + '&&' + str(userReview)
        return redirect(url_for('addReview',reviewData=reviewData))
    bookReviewData = db.execute("SELECT * FROM reviewdata WHERE isbn = :isbn",{"isbn":book_isbn}).fetchall()
    bookObject = CreateBookDataObject(book_isbn)

    return render_template("Book.html",bookdata=bookObject,username=username,reviewdata=bookReviewData)

@app.route("/addReview/<string:reviewData>")
def addReview(reviewData):
    reviewDataList = reviewData.split('&&')
    isbn = reviewDataList[0]
    username = reviewDataList[1]
    rating = reviewDataList[2]
    review = reviewDataList[3]
    bookReviewData = db.execute("SELECT * FROM reviewdata WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    for reviewDetail in bookReviewData:
        if reviewDetail.username == username:
            return render_template("Error.html",Message="User can only add one comment for a book.")
    db.execute("INSERT INTO reviewdata(isbn,review,rating,username) VALUES (:isbn,:review,:rating,:username)",{"isbn":isbn,"review":review,"rating":rating,"username":username})
    db.commit()
    return redirect(url_for("bookData",book_isbn=isbn,username=username))


# API routes
@app.route("/api/<string:isbn>")
def BookDataAPI(isbn):
    bookObject = CreateBookDataObject(isbn)
    if bookObject is None:
        abort(404)
    return jsonify({
        "title": bookObject.title,
        "author": bookObject.author,
        "year": bookObject.year,
        "isbn": bookObject.isbn,
        "review_count": bookObject.ratingsNumber,
        "average_score": bookObject.averageRating
    })

# Functions
def CreateBookDataObject(isbn):
    bookdata = db.execute("SELECT * FROM bookdetails WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if bookdata is None:
        return None
    API_Key = "4DmhCADyQb0roZlW0nQrA"
    goodReadsData = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":API_Key,"isbns":isbn})
    goodReadsJSON = goodReadsData.json()

    averageRating = goodReadsJSON["books"][0]["average_rating"]
    ratingCount = goodReadsJSON["books"][0]["work_ratings_count"]

    bookObject = BookData(bookdata.isbn,bookdata.title,bookdata.author,bookdata.year)
    bookObject.addGoodReadData(averageRating,ratingCount)

    return bookObject