from flask import redirect,render_template,url_for,Blueprint,request,flash, send_file
from flask_login import LoginManager,current_user,login_user,logout_user,login_required
from .database import User,Section,Book,UserBook,Revoked_books,Feedback
from werkzeug.security import generate_password_hash,check_password_hash
from . import db
import base64
import io
from datetime import datetime, timedelta
from sqlalchemy import and_,func
import matplotlib.pyplot as plt


route = Blueprint('route', __name__)

@route.route('/')
def home():
    return render_template('home.html')

@route.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        user = User.query.filter(input_username==User.username).first()
        if user:
            if check_password_hash(user.password_hash, input_password):
                flash("login sucessfully",category='success')
                login_user(user,remember=False)
                id = user.id
                return redirect(f'/user_dashboard/{id}')
            else:
                flash("wrong credentials",category="error")
        else:
            flash("User not registered try to register from signup page",category='error')
            return redirect('/signup')
    return render_template('login.html',user=current_user)


@route.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(username == User.username).first()
        if user:
            flash("Username is already taken try with different name",category='error')
        elif len(password) < 5:
            flash("Password should be of minimum 5 characters", category="error")
        else:
            user = User(username=username,password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
    return render_template('signup.html',user=current_user)






@route.route('/librarian_login',methods=['GET','POST'])
def librarian_login():
    if request.method=='POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        user = User.query.filter(input_username==User.username).first()
        if user:
            if user.is_librarian==True:
                if user.password_hash == input_password:
                    flash("login sucessfully",category='success')
                    login_user(user,remember=False)
                    id = user.id
                    return redirect(f'/librarian_dashboard/{id}')
                else:
                    flash("wrong credentials",category="error")
            else:
                flash("you don't have admin rights",category='error')
        else:
            flash("Admin not registered",category='error')
    return render_template('librarian_login.html',user=current_user)


@route.route('/user_dashboard/<int:id>')
@login_required
def user_dashboard(id):
    user = User.query.filter(id==User.id).first()
    if user.is_librarian==False:
        books = Book.query.filter(Book.id.notin_(db.session.query(UserBook.book_id).filter(UserBook.user_id == current_user.id))).all()

        for book in books:
            if book.book_img:
                book.book_img_encoded = base64.b64encode(book.book_img).decode('utf-8')
        
        if user.user_img:
            user.user_img_encoded = base64.b64encode(user.user_img).decode('utf-8')


        requested_books_count = UserBook.query.filter_by(user_id=id, is_granted=False).count()
        issued_books_count = UserBook.query.filter_by(user_id=id, is_granted=True).count()

        sections = Section.query.all()

        selected_section_filter = request.args.get('section_filter', type=int)
        search_query = request.args.get('query', type=str)

        if selected_section_filter:
            books = [book for book in books if book.section.id == selected_section_filter]

        if search_query:
            search_query_lower = search_query.lower()
            books = [book for book in books if search_query_lower in book.title.lower() or search_query_lower in book.author.lower()]
        return render_template('user_dashboard.html', user=user, books=books, sections=sections, selected_section_filter=selected_section_filter,request_count=requested_books_count,issued_count=issued_books_count)
    else:
        flash("You don't have access to the page.")
        return redirect('/')
    

@route.route('/librarian_dashboard/<int:id>')
@login_required
def librarian_dashboard(id):
    user = User.query.filter(id==User.id).first()
    if user.is_librarian==True:
        books = Book.query.all()
        sections = Section.query.all()
        for book in books:
            if book.book_img:
                book.book_img_encoded = base64.b64encode(book.book_img).decode('utf-8')


        selected_section_filter = request.args.get('section_filter', type=int)
        search_query = request.args.get('query', type=str)

        if selected_section_filter:
            books = [book for book in books if book.section.id == selected_section_filter]

        if search_query:
            search_query_lower = search_query.lower()
            books = [book for book in books if search_query_lower in book.title.lower() or search_query_lower in book.author.lower()]

        return render_template('librarian_dashboard.html', user=user, books=books, sections=sections, selected_section_filter=selected_section_filter)
    else:
        flash("No Permission",category="error")
        return redirect('/')



@route.route('/logout')
def logout():
    logout_user()
    return redirect('/')






@route.route('library_feedback/<int:id>',methods=['GET','POST'])
@login_required
def library_feedback(id):
    if request.method == 'POST':
        search_username = request.form.get('search_username')
        user = User.query.filter_by(username=search_username).first()

        if user:
            user_feedback = Feedback.query.filter_by(user_id=user.id).all()
            return render_template('feedback.html', user_feedback=user_feedback)
        else:
            flash('User not found.', 'error')

    return render_template('feedback.html', user_feedback=None)














@route.route('/library_issued/<int:id>',methods=['GET',"POST"])
@login_required
def library_issued(id):
    if request.method == 'POST':
        search_username = request.form.get('search_username')
        issued_books = UserBook.query.join(User, Book).filter(
            (UserBook.user_id == User.id) &
            (User.username.ilike(f'%{search_username}%'))
        ).all()
        return render_template('library_issued.html', issued_books=issued_books, search_username=search_username)

    return render_template('library_issued.html')


























@route.route('library_stats/<int:id>',methods=['GET',"POST"])
@login_required
def library_stats(id):
    issued_books_by_section = db.session.query(Section, db.func.count(UserBook.id)).\
        join(Book, Section.id == Book.section_id).\
        join(UserBook, Book.id == UserBook.book_id).\
        filter(UserBook.is_granted == True).\
        group_by(Section.id).all()

    labels_issued_books = [section.name for section, count in issued_books_by_section]
    counts_issued_books = [count for section, count in issued_books_by_section]

    fig_issued_books, ax_issued_books = plt.subplots()
    ax_issued_books.bar(labels_issued_books, counts_issued_books)
    ax_issued_books.set_title('Number of Issued Books per Section')
    ax_issued_books.set_xlabel('Section')
    ax_issued_books.set_ylabel('Number of Books')

    img_buf_issued_books = io.BytesIO()
    plt.savefig(img_buf_issued_books, format='png')
    img_buf_issued_books.seek(0)
    img_base64_issued_books = base64.b64encode(img_buf_issued_books.read()).decode('utf-8')


    now = datetime.now()
    date_labels = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]

    counts_issued_books = []
    for date_label in date_labels:
        start_date = datetime.strptime(date_label, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        
        issued_books_on_date = UserBook.query.filter(
            UserBook.is_granted.isnot(None),
            UserBook.issued_at.between(start_date, end_date)
        ).count()
        
        counts_issued_books.append(issued_books_on_date)

    print("Counts of Issued Books:", counts_issued_books)

    fig_issued_books, ax_issued_books = plt.subplots(figsize=(10,6))
    line = ax_issued_books.plot(date_labels, counts_issued_books, marker='o', color='#ff9999', label='Issued Books')
    ax_issued_books.set_xlabel('Date')
    ax_issued_books.set_ylabel('Number of Issued Books')
    ax_issued_books.set_title('Issued Books Trend Over the Last 7 Days')
    ax_issued_books.legend()

    img_buf_active_books = io.BytesIO()
    plt.savefig(img_buf_active_books, format='png')
    img_buf_active_books.seek(0)
    img_base64_active_books = base64.b64encode(img_buf_active_books.read()).decode('utf-8')

    return render_template('library_stats.html',img_base64_issued_books=img_base64_issued_books,img_base64_active_books=img_base64_active_books)








@route.route('stats/<int:id>',methods=['GET','POST'])
@login_required
def stats(id):
    user = User.query.get(id)
    user_books_count = UserBook.query.filter_by(user_id=id,is_granted=True).count()
    requested_books_count = UserBook.query.filter_by(user_id=id, is_granted=False).count()
    revoked_books_count = Revoked_books.query.filter_by(user_id=id).count()
    fig, ax = plt.subplots()
    ax.bar(['Issued Books', 'Requested Books',"Revoked_Books"], [user_books_count, requested_books_count,revoked_books_count], color=['blue', 'red','green'])
    ax.set_ylabel('Number of Books')
    img_buf_books_overview = io.BytesIO()
    plt.savefig(img_buf_books_overview, format='png')
    img_buf_books_overview.seek(0)
    img_base64_books_overview = base64.b64encode(img_buf_books_overview.read()).decode('utf-8')

    
    issued_books_by_section = db.session.query(Section.name, func.count(Book.id)).\
    join(Book, Section.id == Book.section_id).\
    join(UserBook, Book.id == UserBook.book_id).\
    filter(UserBook.user_id == id).\
    group_by(Section.id).all()

    labels = [section[0] for section in issued_books_by_section]
    sizes = [section[1] for section in issued_books_by_section]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'] 
    explode = [0.1] * len(labels)
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    img_buf_books_by_section = io.BytesIO()
    plt.savefig(img_buf_books_by_section, format='png')
    img_buf_books_by_section.seek(0)
    img_base64_books_by_section = base64.b64encode(img_buf_books_by_section.read()).decode('utf-8')


    return render_template('stats.html',user=user,img_base64=img_base64_books_overview,img_base64_books_by_section=img_base64_books_by_section)






@route.route('upload_user_image/<int:id>',methods=["POST"])
@login_required
def upload_user_image(id):
    user_img = request.files['upload_user_img'].read()
    user = User.query.get(id)
    
    if user:
        user.user_img = user_img
        db.session.commit()
        flash("Profile photo uploaded successfully",'success')
    
    return redirect(url_for('route.user_dashboard',id=current_user.id))


@route.route('delete_profile_photo/<int:id>',methods=['GET','POST'])
@login_required
def delete_profile_photo(id):
    user = User.query.get(id)
    user.user_img = None
    db.session.commit()
    flash('Profile deleted successfully','success')
    return redirect(url_for('route.user_dashboard',id=current_user.id))




@route.route('/request_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def request_book(book_id):
    book = Book.query.get_or_404(book_id)

    existing_request = UserBook.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if existing_request:
        flash('You have already requested this book.', category='error')
        return redirect(url_for('route.user_dashboard',id=current_user.id))

    if len(current_user.user_books) >= 5:
        flash('You have reached the maximum limit of requested books (5).',category='error')
        return redirect(url_for('route.user_dashboard',id=current_user.id))


    new_request = UserBook(user_id=current_user.id, book_id=book.id)
    db.session.add(new_request)
    db.session.commit()

    flash('Book request submitted successfully!', 'success')
    return redirect(url_for('route.user_dashboard',id=current_user.id))



@route.route('/my_books/<int:id>',methods=['GET','POST'])
@login_required
def my_books(id):
    requested_books = UserBook.query.filter_by(user_id=id, is_granted=False).all()
    for book in requested_books:
        if book.book.book_img:
            book.book.book_img_encoded = base64.b64encode(book.book.book_img).decode('utf-8')

    

    issued_books = UserBook.query.filter_by(user_id=id, is_granted=True).all()
    for book in issued_books:
        if book.book.book_img:
            book.book.book_img_encoded = base64.b64encode(book.book.book_img).decode('utf-8')

    revoked_books = Revoked_books.query.filter(Revoked_books.user_id == id).all()
    for book in revoked_books:
        if book.book.book_img:
            book.book.book_img_encoded = base64.b64encode(book.book.book_img).decode('utf-8')



    return render_template('my_books.html', requested_books=requested_books, issued_books=issued_books,revoked_books=revoked_books)



@route.route('/requested_books/<int:id>')
@login_required
def requested_books(id):
    user = User.query.filter_by(id=id).first()

    if user.is_librarian:
        search_term = request.args.get('search_term', None)

        if search_term:
            requested_books = UserBook.query.filter(UserBook.is_granted == False,UserBook.user.has(username=search_term)).all()
        else:
            requested_books = UserBook.query.filter_by(is_granted=False).all()

        for book in requested_books:
            if book.book.book_img:
                book.book.book_img_encoded = base64.b64encode(book.book.book_img).decode('utf-8')


        return render_template('requests.html', user=user, requested_books=requested_books)
    else:
        flash("No Permission", category="error")








@route.route('/accept_request/<int:user_book_id>')
@login_required
def accept_request(user_book_id):
    requested_book = UserBook.query.get(user_book_id)

    if requested_book:
        requested_book.is_granted = True
        requested_book.issued_at = datetime.now()
        requested_book.access_end_date = datetime.now() + timedelta(days=7)
        db.session.commit()

        flash('Book request accepted successfully!', 'success')
    else:
        flash('Book request not found.', 'error')

    return redirect(url_for('route.requested_books', id=current_user.id))

@route.route('/accept_with_download/<int:user_book_id>')
@login_required
def accept_with_download(user_book_id):
    requested_book = UserBook.query.get(user_book_id)

    if requested_book:
        requested_book.is_granted = True
        requested_book.issued_at = datetime.now()
        requested_book.access_end_date = datetime.max
        requested_book.downloadable = True
        db.session.commit()

        flash('Book request accepted successfully!', 'success')
    else:
        flash('Book request not found.', 'error')

    return redirect(url_for('route.requested_books', id=current_user.id))




@route.route('/reject_request/<int:user_book_id>')
@login_required
def reject_request(user_book_id):
    if not current_user.is_librarian:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('index'))

    requested_book = UserBook.query.get(user_book_id)

    if requested_book:
        db.session.delete(requested_book)
        db.session.commit()

        flash('Book request rejected successfully!', 'warning')
    else:
        flash('Book request not found.', 'error')

    return redirect(url_for('route.requested_books', id=current_user.id))



@route.route('cancel_request/<int:user_book_id>', methods=['GET', 'POST'])
@login_required
def cancel_request(user_book_id):
    user_book = UserBook.query.get_or_404(user_book_id)

    if user_book.is_granted:
        flash('This book request has already been granted and cannot be canceled.', 'warning')
        return redirect(url_for('route.my_books', id=current_user.id))

    db.session.delete(user_book)
    db.session.commit()

    flash('Book request canceled successfully!', 'success')
    return redirect(url_for('route.my_books', id=current_user.id))




@route.route('return_book/<int:user_book_id>', methods=['GET', 'POST'])
@login_required
def return_book(user_book_id):
    user_book = UserBook.query.get_or_404(user_book_id)

    
    if user_book.is_granted:
        db.session.delete(user_book)
        db.session.commit()
        flash('Book returned successfully',category='success')
    else:
        flash('some error occured','error')
        
    return redirect(url_for('route.my_books', id=current_user.id))



@route.route('feedback_submit/<int:user_book_id>/',methods=['POST'])
@login_required
def feedback_submit(user_book_id):
    feed = request.form.get('feedback')
    userbook = UserBook.query.get(user_book_id)
    feedback = Feedback.query.get(user_book_id)
    
    if feedback:
        feedback.feedback = feed
        db.session.commit()
        flash("Feedback updated", "success")
        return redirect(url_for('route.my_books', id=user_book_id))
    else:
        feedback = Feedback(user_id=userbook.user_id, book_id=userbook.book_id, feedback=feed, user_book_id=user_book_id)
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback added successfully", "success")
        return redirect(url_for('route.my_books', id=user_book_id))
    
    









# Librarian Funcationality


@route.route('add_section', methods=['POST'])
@login_required
def add_section():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['Description']
        section=None
        section = Section.query.filter_by(name=name).first()
        if section:
            flash("This section already exits. Section should be unique!", category='error')
            return redirect(url_for('route.librarian_dashboard',id=current_user.id))
        else:
            section = Section(name=name,description=description)
            db.session.add(section)
            db.session.commit()
            flash("Section created in the database.")
            return redirect(url_for('route.librarian_dashboard',id=current_user.id))
        

@route.route('/update_section', methods=['POST'])
@login_required
def update_section():
    update_section_id = request.form.get('update_section_id')
    new_section_name = request.form.get('update_name')
    new_section_description = request.form.get('update_description')

    section_to_update = Section.query.get(update_section_id)
    
    if section_to_update:
        section_to_update.name = new_section_name
        section_to_update.description = new_section_description
        db.session.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('route.librarian_dashboard',id=current_user.id))
    else:
        flash('Section not found or could not be updated.', 'error')


@route.route('/delete_section', methods=['POST'])
@login_required
def delete_section():
    delete_section_id = request.form.get('delete_section_id')

    section_to_delete = Section.query.get(delete_section_id)
    
    if section_to_delete:
        books_to_delete = Book.query.filter_by(section_id=delete_section_id).all()
        for book in books_to_delete:
            db.session.delete(book)

        db.session.delete(section_to_delete)
        db.session.commit()
        flash('Section deleted successfully!', 'success')
        return redirect(url_for('route.librarian_dashboard',id=current_user.id))
    else:
        flash('Section not found or could not be deleted.', 'error')

        

# book funcationalities

@route.route('/add_book', methods=['POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        pdf_link = request.form['pdf_link']
        section_id = request.form['section_id']
        price = request.form['price']

        
        book_img = request.files['book_img'].read()
        book_pdf = request.files['book_pdf'].read()

        
        existing_book = Book.query.filter_by(title=title).first()
        if existing_book:
            flash("A book with this title already exists. Please choose a different title.", category='error')
            return redirect(url_for('route.librarian_dashboard',id=current_user.id))  # Adjust the route accordingly

        new_book = Book(title=title, author=author, pdf_link=pdf_link, 
                        book_img=book_img, book_pdf=book_pdf, section_id=section_id,price=price)

        db.session.add(new_book)
        db.session.commit()
        flash("Book added to the section")
        return redirect(url_for('route.librarian_dashboard',id=current_user.id))
    

    


# Update Book
@route.route('/update_book', methods=['POST'])
@login_required
def update_book():
    update_book_id = request.form.get('update_book_id')
    new_title = request.form.get('update_title')
    new_author = request.form.get('update_author')
    new_pdf_link = request.form.get('update_pdf_link')
    new_section_id = request.form.get('update_section_id')
    price = request.form.get('update_price')

    book_to_update = Book.query.get(update_book_id)
    
    if book_to_update:
        book_to_update.title = new_title
        book_to_update.author = new_author
        book_to_update.pdf_link = new_pdf_link
        book_to_update.section_id = new_section_id
        book_to_update.price = price

        
        if 'update_book_img' in request.files:
            book_to_update.book_img = request.files['update_book_img'].read()
        if 'update_book_pdf' in request.files:
            book_to_update.book_pdf = request.files['update_book_pdf'].read()

        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('route.librarian_dashboard', id=current_user.id))
    else:
        flash('Book not found or could not be updated.', 'error')
        return redirect(url_for('route.librarian_dashboard', id=current_user.id))


# Delete Book
@route.route('/delete_book', methods=['POST'])
@login_required
def delete_book():
    delete_book_id = request.form.get('delete_book_id')

    book_to_delete = Book.query.get(delete_book_id)
    
    if book_to_delete:
        db.session.delete(book_to_delete)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
        return redirect(url_for('route.librarian_dashboard', id=current_user.id))
    else:
        flash('Book not found or could not be deleted.', 'error')
        return redirect(url_for('route.librarian_dashboard', id=current_user.id))
    


@route.route('/download_pdf/<int:book_id>')
def download_pdf(book_id):
    book = Book.query.get_or_404(book_id)
    return send_file(
        io.BytesIO(book.book_pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{book.title}.pdf'
    )

