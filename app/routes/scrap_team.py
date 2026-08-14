from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Byproduct, Batch, RawMaterial
from app.utils.decorators import role_required
from app.utils.byproduct_algo import recommend_byproduct_use, get_recommendation_display
from datetime import datetime
from sqlalchemy import func

scrap_bp = Blueprint('scrap', __name__)


@scrap_bp.route('/dashboard')
@login_required
@role_required('scrap_team')
def dashboard():
    # Stats for scrap team
    assigned_batches = Byproduct.query.filter_by(assigned_to=current_user.id)
    total_assigned = assigned_batches.count()
    pending_count = assigned_batches.filter_by(status='assigned').count()
    in_treatment_count = assigned_batches.filter_by(status='in_treatment').count()
    completed_count = assigned_batches.filter_by(status='completed').count()

    # Recent assigned byproducts
    recent_byproducts = assigned_batches.order_by(
        Byproduct.created_at.desc()
    ).limit(5).all()

    # Total weight processed
    total_weight = db.session.query(
        func.sum(Byproduct.quantity_kg)
    ).filter_by(assigned_to=current_user.id).scalar() or 0

    total_secondary_output = db.session.query(
        func.sum(Byproduct.secondary_output_kg)
    ).filter_by(assigned_to=current_user.id).scalar() or 0

    # By-product type breakdown
    type_breakdown = db.session.query(
        Byproduct.byproduct_type,
        func.count(Byproduct.id).label('count'),
        func.sum(Byproduct.quantity_kg).label('total_kg')
    ).filter_by(assigned_to=current_user.id).group_by(Byproduct.byproduct_type).all()

    # Recommendation breakdown
    rec_breakdown = db.session.query(
        Byproduct.recommended_use,
        func.count(Byproduct.id).label('count')
    ).filter_by(assigned_to=current_user.id).group_by(Byproduct.recommended_use).all()

    rec_labels = [get_recommendation_display(r.recommended_use) for r in rec_breakdown]
    rec_values = [r.count for r in rec_breakdown]

    return render_template('scrap_team/dashboard.html',
                           total_assigned=total_assigned,
                           pending_count=pending_count,
                           in_treatment_count=in_treatment_count,
                           completed_count=completed_count,
                           recent_byproducts=recent_byproducts,
                           total_weight=float(total_weight),
                           total_secondary_output=float(total_secondary_output),
                           type_breakdown=type_breakdown,
                           rec_labels=rec_labels,
                           rec_values=rec_values)


@scrap_bp.route('/batches')
@login_required
@role_required('scrap_team')
def batches():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    query = Byproduct.query.filter_by(assigned_to=current_user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    byproducts = query.order_by(Byproduct.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('scrap_team/batches.html',
                           byproducts=byproducts,
                           status_filter=status_filter)


@scrap_bp.route('/byproduct/<int:bp_id>')
@login_required
@role_required('scrap_team')
def byproduct_detail(bp_id):
    byproduct = Byproduct.query.get_or_404(bp_id)

    # Ensure scrap team member can only see their assigned byproducts
    if byproduct.assigned_to != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('scrap.dashboard'))

    # Get recommendation details
    recommendation = recommend_byproduct_use(
        byproduct.byproduct_type,
        iron_oxide_percent=float(byproduct.iron_oxide_percent or 0),
        alumina_percent=float(byproduct.alumina_percent or 0),
        silica_percent=float(byproduct.silica_percent or 0),
        manganese_percent=float(byproduct.manganese_percent or 0),
        rare_earth_percent=float(byproduct.rare_earth_percent or 0)
    )

    return render_template('scrap_team/byproduct_detail.html',
                           byproduct=byproduct,
                           recommendation=recommendation)


@scrap_bp.route('/log-treatment/<int:bp_id>', methods=['POST'])
@login_required
@role_required('scrap_team')
def log_treatment(bp_id):
    byproduct = Byproduct.query.get_or_404(bp_id)

    if byproduct.assigned_to != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('scrap.dashboard'))

    action = request.form.get('action')

    if action == 'start':
        byproduct.status = 'in_treatment'
        db.session.commit()
        flash('Treatment started.', 'info')

    elif action == 'complete':
        treatment_result = request.form.get('treatment_result', '')
        secondary_output_kg = request.form.get('secondary_output_kg')
        actual_use = request.form.get('actual_use')

        if not treatment_result:
            flash('Please provide treatment result details.', 'danger')
            return redirect(url_for('scrap.byproduct_detail', bp_id=bp_id))

        byproduct.status = 'completed'
        byproduct.treatment_result = treatment_result
        byproduct.treatment_completed_at = datetime.utcnow()

        if secondary_output_kg:
            try:
                byproduct.secondary_output_kg = float(secondary_output_kg)
            except ValueError:
                pass

        if actual_use:
            byproduct.recommended_use = actual_use

        db.session.commit()
        flash('Treatment completed and logged successfully.', 'success')

    elif action == 'dispose':
        byproduct.status = 'disposed'
        byproduct.treatment_result = request.form.get('disposal_notes', 'Disposed safely')
        byproduct.treatment_completed_at = datetime.utcnow()
        db.session.commit()
        flash('By-product marked as disposed.', 'info')

    return redirect(url_for('scrap.byproduct_detail', bp_id=bp_id))


@scrap_bp.route('/queue')
@login_required
@role_required('scrap_team')
def queue():
    """View all pending/unassigned byproducts (for team awareness)."""
    page = request.args.get('page', 1, type=int)

    # Show assigned to current user + unassigned
    byproducts = Byproduct.query.filter(
        (Byproduct.assigned_to == current_user.id) |
        (Byproduct.status == 'pending')
    ).order_by(Byproduct.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('scrap_team/queue.html', byproducts=byproducts)
