import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    file = open("books.csv",'r')
    reader = csv.reader(file)
    count = 1
    for isbn,title,author,year in reader:
        db.execute("INSERT INTO bookdetails (isbn,title,author,year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"{isbn}-{title}-{author}-{year} => count: {count}")
        count +=1
    db.commit()

if __name__ == "__main__":
    main()