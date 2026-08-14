from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import User, Role, RawMaterial, Batch, Byproduct, YieldPrediction, AdminLog
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func
import io

admin_bp = Blueprint('admin', __name__)


def log_action(action, target_type=None, target_id=None, details=None):
    """Log admin action."""
    log = AdminLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Stats
    total_users = User.query.filter_by(is_admin=False).count()
    pending_users = User.query.filter_by(is_approved=False, is_active=True).count()
    total_materials = RawMaterial.query.count()
    total_batches = Batch.query.count()
    completed_batches = Batch.query.filter_by(status='completed').count()
    active_batches = Batch.query.filter(
        Batch.status.in_(['digestion', 'clarification', 'precipitation', 'calcination'])
    ).count()
    total_byproducts = Byproduct.query.count()
    pending_byproducts = Byproduct.query.filter_by(status='pending').count()

    # Recent activity
    recent_materials = RawMaterial.query.order_by(RawMaterial.created_at.desc()).limit(5).all()
    recent_batches = Batch.query.order_by(Batch.created_at.desc()).limit(5).all()
    pending_registrations = User.query.filter_by(is_approved=False, is_active=True).order_by(
        User.created_at.desc()
    ).limit(5).all()

    # Yield trend data (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    yield_data = db.session.query(
        func.date(Batch.created_at).label('date'),
        func.avg(Batch.actual_yield_percent).label('avg_yield')
    ).filter(
        Batch.created_at >= thirty_days_ago,
        Batch.actual_yield_percent.isnot(None)
    ).group_by(func.date(Batch.created_at)).order_by('date').all()

    yield_labels = [str(row.date) for row in yield_data]
    yield_values = [float(row.avg_yield) if row.avg_yield else 0 for row in yield_data]

    # By-product breakdown
    byproduct_counts = db.session.query(
        Byproduct.byproduct_type,
        func.count(Byproduct.id).label('count')
    ).group_by(Byproduct.byproduct_type).all()

    bp_labels = [row.byproduct_type.replace('_', ' ').title() for row in byproduct_counts]
    bp_values = [row.count for row in byproduct_counts]

    # Total weight processed
    total_weight = db.session.query(func.sum(RawMaterial.weight_kg)).scalar() or 0

    # Average yield
    avg_yield = db.session.query(func.avg(Batch.actual_yield_percent)).filter(
        Batch.actual_yield_percent.isnot(None)
    ).scalar() or 0

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           pending_users=pending_users,
                           total_materials=total_materials,
                           total_batches=total_batches,
                           completed_batches=completed_batches,
                           active_batches=active_batches,
                           total_byproducts=total_byproducts,
                           pending_byproducts=pending_byproducts,
                           recent_materials=recent_materials,
                           recent_batches=recent_batches,
                           pending_registrations=pending_registrations,
                           yield_labels=yield_labels,
                           yield_values=yield_values,
                           bp_labels=bp_labels,
                           bp_values=bp_values,
                           total_weight=float(total_weight),
                           avg_yield=float(avg_yield))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    role_filter = request.args.get('role', 'all')
    search = request.args.get('search', '')

    query = User.query.filter_by(is_admin=False)

    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif status_filter == 'active':
        query = query.filter_by(is_approved=True, is_active=True)
    elif status_filter == 'suspended':
        query = query.filter_by(is_active=False)

    if role_filter != 'all':
        role = Role.query.filter_by(name=role_filter).first()
        if role:
            query = query.filter_by(role_id=role.id)

    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )

    users_paginated = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    roles = Role.query.all()

    return render_template('admin/users.html',
                           users=users_paginated,
                           roles=roles,
                           status_filter=status_filter,
                           role_filter=role_filter,
                           search=search)


@admin_bp.route('/users/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    db.session.commit()
    log_action('approve_user', 'user', user_id, f'Approved user: {user.username}')
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    log_action('reject_user', 'user', user_id, f'Rejected and deleted user registration')
    flash('User registration has been rejected and removed.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/suspend/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    log_action('suspend_user', 'user', user_id, f'Suspended user: {user.username}')
    flash(f'User {user.username} has been suspended.', 'warning')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/activate/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    log_action('activate_user', 'user', user_id, f'Activated user: {user.username}')
    flash(f'User {user.username} has been activated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/batches')
@login_required
@admin_required
def batches():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    query = Batch.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    batches_paginated = query.order_by(Batch.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template('admin/batches.html',
                           batches=batches_paginated,
                           status_filter=status_filter)


@admin_bp.route('/byproducts')
@login_required
@admin_required
def byproducts():
    page = request.args.get('page', 1, type=int)
    byproducts_paginated = Byproduct.query.order_by(Byproduct.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    scrap_team_users = User.query.join(Role).filter(Role.name == 'scrap_team',
                                                     User.is_approved == True).all()
    return render_template('admin/byproducts.html',
                           byproducts=byproducts_paginated,
                           scrap_team_users=scrap_team_users)


@admin_bp.route('/byproducts/assign/<int:bp_id>', methods=['POST'])
@login_required
@admin_required
def assign_byproduct(bp_id):
    byproduct = Byproduct.query.get_or_404(bp_id)
    user_id = request.form.get('user_id')
    if user_id:
        byproduct.assigned_to = int(user_id)
        byproduct.status = 'assigned'
        db.session.commit()
        log_action('assign_byproduct', 'byproduct', bp_id, f'Assigned to user {user_id}')
        flash('By-product assigned successfully.', 'success')
    return redirect(url_for('admin.byproducts'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    # Summary stats for reports page
    total_materials = RawMaterial.query.count()
    total_weight = db.session.query(func.sum(RawMaterial.weight_kg)).scalar() or 0
    total_batches = Batch.query.count()
    completed_batches = Batch.query.filter_by(status='completed').count()
    avg_yield = db.session.query(func.avg(Batch.actual_yield_percent)).filter(
        Batch.actual_yield_percent.isnot(None)
    ).scalar() or 0
    total_byproducts = Byproduct.query.count()
    total_byproduct_weight = db.session.query(func.sum(Byproduct.quantity_kg)).scalar() or 0

    recent_batches = Batch.query.order_by(Batch.created_at.desc()).limit(10).all()

    return render_template('admin/reports.html',
                           total_materials=total_materials,
                           total_weight=float(total_weight),
                           total_batches=total_batches,
                           completed_batches=completed_batches,
                           avg_yield=float(avg_yield),
                           total_byproducts=total_byproducts,
                           total_byproduct_weight=float(total_byproduct_weight),
                           recent_batches=recent_batches)


@admin_bp.route('/reports/pdf')
@login_required
@admin_required
def generate_pdf():
    """Generate PDF report."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=20, spaceAfter=12, alignment=TA_CENTER,
                                     textColor=colors.HexColor('#1a3a5c'))
        story.append(Paragraph('SAEROS - System Report', title_style))
        story.append(Paragraph(f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}',
                               styles['Normal']))
        story.append(Spacer(1, 20))

        # Summary stats
        story.append(Paragraph('Summary Statistics', styles['Heading2']))

        total_materials = RawMaterial.query.count()
        total_weight = db.session.query(func.sum(RawMaterial.weight_kg)).scalar() or 0
        total_batches = Batch.query.count()
        completed_batches = Batch.query.filter_by(status='completed').count()
        avg_yield = db.session.query(func.avg(Batch.actual_yield_percent)).filter(
            Batch.actual_yield_percent.isnot(None)
        ).scalar() or 0

        summary_data = [
            ['Metric', 'Value'],
            ['Total Raw Materials', str(total_materials)],
            ['Total Weight Processed (kg)', f'{float(total_weight):,.2f}'],
            ['Total Batches', str(total_batches)],
            ['Completed Batches', str(completed_batches)],
            ['Average Yield (%)', f'{float(avg_yield):.2f}%'],
        ]

        table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f4f8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Recent batches
        story.append(Paragraph('Recent Batches', styles['Heading2']))
        recent_batches = Batch.query.order_by(Batch.created_at.desc()).limit(10).all()

        batch_data = [['Batch #', 'Status', 'Input (kg)', 'Output (kg)', 'Yield %', 'Date']]
        for b in recent_batches:
            batch_data.append([
                b.batch_number,
                b.status.replace('_', ' ').title(),
                f'{float(b.total_input_weight):,.1f}' if b.total_input_weight else 'N/A',
                f'{float(b.total_output_weight):,.1f}' if b.total_output_weight else 'N/A',
                f'{float(b.actual_yield_percent):.1f}%' if b.actual_yield_percent else 'N/A',
                b.created_at.strftime('%Y-%m-%d') if b.created_at else 'N/A'
            ])

        if len(batch_data) > 1:
            batch_table = Table(batch_data, colWidths=[1.2 * inch, 1 * inch, 1 * inch,
                                                        1 * inch, 0.8 * inch, 1 * inch])
            batch_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a9f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(batch_table)

        doc.build(story)
        buffer.seek(0)

        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=saeros_report_{datetime.utcnow().strftime("%Y%m%d")}.pdf'
        )
        log_action('generate_pdf_report', details='Generated system PDF report')
        return response

    except ImportError:
        flash('PDF generation requires reportlab. Install it with: pip install reportlab', 'warning')
        return redirect(url_for('admin.reports'))


@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs_paginated = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/logs.html', logs=logs_paginated)


@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard chart data."""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Weekly yield trend
    yield_data = db.session.query(
        func.date(Batch.created_at).label('date'),
        func.avg(Batch.actual_yield_percent).label('avg_yield'),
        func.count(Batch.id).label('count')
    ).filter(
        Batch.created_at >= start_date,
        Batch.actual_yield_percent.isnot(None)
    ).group_by(func.date(Batch.created_at)).order_by('date').all()

    return jsonify({
        'yield_trend': {
            'labels': [str(row.date) for row in yield_data],
            'values': [float(row.avg_yield) if row.avg_yield else 0 for row in yield_data],
            'counts': [row.count for row in yield_data]
        }
    })
