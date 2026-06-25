from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'snowix-secret-key-change-this'
# Using absolute path for database to avoid instance/ folder confusion if needed
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'snowix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# ── MODELS ──────────────────────────────────────────────
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def formatted_date(self):
        return self.created_at.strftime('%d.%m.%Y')

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── ADMIN AUTH ───────────────────────────────────────────
ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'snowix2025'  # поменяй!

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ROUTES ────────────────────────────────────────
@app.route('/')
def glavnoe():
    return render_template('glavnoe.html', page='главное')

@app.route('/pravila')
def pravila():
    return render_template('pravila.html', page='правила')

@app.route('/sborka')
def sborka():
    return render_template('sborka.html', page='сборка')

@app.route('/novosti')
def novosti():
    page = request.args.get('p', 1, type=int)
    news = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=4)
    return render_template('novosti.html', page='новости', news=news)

@app.route('/novosti/<int:news_id>')
def news_detail(news_id):
    item = News.query.get_or_404(news_id)
    return render_template('news_detail.html', page='новости', item=item)

@app.route('/galereya')
def galereya():
    page = request.args.get('p', 1, type=int)
    per_page = 8
    images_pagination = Gallery.query.order_by(Gallery.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('galereya.html', page='галерея', images=images_pagination)

@app.route('/karta')
def karta():
    return render_template('karta.html', page='карта')

@app.route('/donat')
def donat():
    return render_template('donat.html', page='донат')

# ── ADMIN ROUTES ─────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['login'] == ADMIN_LOGIN and
                request.form['password'] == ADMIN_PASSWORD):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Неверный логин или пароль')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    news = News.query.order_by(News.created_at.desc()).all()
    gallery = Gallery.query.order_by(Gallery.created_at.desc()).all()
    return render_template('admin/dashboard.html', news=news, gallery=gallery)

def save_picture(form_picture):
    if not os.path.exists(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])):
        os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))

    filename = secure_filename(form_picture.filename)
    picture_fn = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + filename
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_news_add():
    if request.method == 'POST':
        created_at_str = request.form.get('created_at')
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

        picture_file = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                picture_file = save_picture(file)

        item = News(
            title=request.form['title'],
            content=request.form['content'],
            image_file=picture_file,
            created_at=created_at
        )
        db.session.add(item)
        db.session.commit()
        flash('Новость опубликована!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/news_form.html', item=None)

@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def admin_news_edit(news_id):
    item = News.query.get_or_404(news_id)
    if request.method == 'POST':
        item.title = request.form['title']
        item.content = request.form['content']

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                item.image_file = save_picture(file)

        created_at_str = request.form.get('created_at')
        if created_at_str:
            item.created_at = datetime.fromisoformat(created_at_str)
        db.session.commit()
        flash('Новость обновлена!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/news_form.html', item=item)

@app.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@login_required
def admin_news_delete(news_id):
    item = News.query.get_or_404(news_id)
    db.session.delete(item)
    db.session.commit()
    flash('Новость удалена')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/gallery/add', methods=['GET', 'POST'])
@login_required
def admin_gallery_add():
    if request.method == 'POST':
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                picture_file = save_picture(file)
                item = Gallery(image_file=picture_file)
                db.session.add(item)
                db.session.commit()
                flash('Фото добавлено в галерею!')
                return redirect(url_for('admin_dashboard'))
        flash('Ошибка при загрузке фото')
    return render_template('admin/gallery_form.html')

@app.route('/admin/gallery/delete/<int:image_id>', methods=['POST'])
@login_required
def admin_gallery_delete(image_id):
    item = Gallery.query.get_or_404(image_id)
    db.session.delete(item)
    db.session.commit()
    flash('Фото удалено из галереи')
    return redirect(url_for('admin_dashboard'))

# ── INIT ─────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
