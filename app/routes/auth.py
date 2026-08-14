from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, Role, AdminLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact the administrator.', 'danger')
                return render_template('login.html')

            if not user.is_approved:
                flash('Your account is pending administrator approval. Please wait.', 'warning')
                return render_template('login.html')

            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('auth.dashboard_redirect'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    roles = Role.query.filter(Role.name != 'admin').all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        role_id = request.form.get('role_id')
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not full_name:
            errors.append('Full name is required.')
        if not role_id:
            errors.append('Please select a role.')

        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', roles=roles)

        # Create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role_id=int(role_id),
            phone=phone,
            department=department,
            is_approved=False,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Your account is pending admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', roles=roles)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/pending')
def pending():
    return render_template('pending.html')


@auth_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect to role-specific dashboard."""
    if not current_user.is_approved:
        return redirect(url_for('auth.pending'))

    role = current_user.get_role_name()
    if role == 'admin' or current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif role == 'agent':
        return redirect(url_for('agent.dashboard'))
    elif role == 'scrap_team':
        return redirect(url_for('scrap.dashboard'))
    else:
        flash('Unknown role. Please contact administrator.', 'danger')
        return redirect(url_for('auth.login'))
