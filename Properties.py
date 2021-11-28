class BookData:

    def __init__(self,isbn,title,author,year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year

    def addGoodReadData(self,averageRating,ratingsNumber):
        self.averageRating = averageRating
        self.ratingsNumber = ratingsNumber


