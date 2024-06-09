from app import create_all

app = create_all()

from app import db 
from app.database import UserBook,Revoked_books,User
from datetime import datetime


def revoke_expired_access():
    expired_books = UserBook.query.filter(UserBook.is_granted == True, UserBook.access_end_date <= datetime.now()).all()

    for book in expired_books:
        revoked_book = Revoked_books(book_id = book.book_id, user_id = book.user_id, revoked_on=book.access_end_date,revoke_message="Access revoked due to expiration")
        db.session.add(revoked_book)
        db.session.commit()
        db.session.delete(book)
        db.session.commit()
def admin_create():
    libraian = User.query.all()
    if libraian:
        return 
    else:
        librarian = User(username="harsh",password_hash="1234567",is_librarian=True)
        db.session.add(librarian)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        revoke_expired_access()
        admin_create()
    app.run(debug=True)