from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def role_required(*roles):
    """Decorator to restrict access to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.is_approved:
                flash('Your account is pending admin approval.', 'warning')
                return redirect(url_for('auth.pending'))
            if not current_user.is_active:
                flash('Your account has been suspended. Contact admin.', 'danger')
                return redirect(url_for('auth.login'))
            if current_user.get_role_name() not in roles and not current_user.is_admin:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to restrict access to admins only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        if not current_user.is_active:
            flash('Your account has been suspended.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def approved_required(f):
    """Decorator to ensure user is approved."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_approved:
            flash('Your account is pending admin approval.', 'warning')
            return redirect(url_for('auth.pending'))
        if not current_user.is_active:
            flash('Your account has been suspended.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
