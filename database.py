from flask_login import UserMixin
from . import db
from datetime import datetime
import threading


class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_img = db.Column(db.LargeBinary,nullable=True)
    is_librarian = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), default = datetime.now())
    user_books = db.relationship('UserBook', backref='user', lazy=True)
    revoked_books = db.relationship('Revoked_books', backref='user', lazy=True)
    feedback = db.relationship('Feedback', backref='user', lazy=True)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text,nullable=False)
    date = db.Column(db.DateTime(timezone=True), default = datetime.now())
    books = db.relationship('Book', backref='section', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    pdf_link = db.Column(db.Text, nullable=False)
    book_img = db.Column(db.LargeBinary)
    book_pdf = db.Column(db.LargeBinary)
    author = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer,nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    user_books = db.relationship('UserBook', backref='book', lazy=True)
    revoked_books = db.relationship('Revoked_books', backref='book', lazy=True)
    feedback = db.relationship('Feedback', backref='book', lazy=True)



class UserBook(db.Model):
    __tablename__ = 'user_book'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    is_granted = db.Column(db.Boolean, default=False)
    downloadable = db.Column(db.Boolean, default=False)
    issued_at = db.Column(db.DateTime(timezone=True), nullable=True)
    access_end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    feedback = db.relationship('Feedback', backref='userbook', lazy=True)

    

class Revoked_books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    revoked_on =  db.Column(db.DateTime(timezone=True), nullable=True)
    revoke_message = db.Column(db.Text,nullable=True)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=True)
    user_book_id = db.Column(db.Integer, db.ForeignKey('user_book.id'), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    

