from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'snowix-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///snowix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── MODELS ──────────────────────────────────────────────
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def formatted_date(self):
        return self.created_at.strftime('%d.%m.%Y')

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
    gallery_dir = os.path.join(app.static_folder, 'images', 'gallery')
    all_images = []
    if os.path.exists(gallery_dir):
        all_images = sorted([f for f in os.listdir(gallery_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])

    total = len(all_images)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    images = all_images[start:end]

    return render_template('galereya.html', page='галерея', images=images, current_page=page, total_pages=pages)

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
    return render_template('admin/dashboard.html', news=news)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_news_add():
    if request.method == 'POST':
        item = News(
            title=request.form['title'],
            content=request.form['content']
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

# ── INIT ─────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
