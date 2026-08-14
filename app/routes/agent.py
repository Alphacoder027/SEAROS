from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import RawMaterial, Batch, BayerProcessLog, Byproduct, YieldPrediction
from app.utils.decorators import role_required
from app.utils.ml_model import predict_yield
from app.utils.byproduct_algo import recommend_byproduct_use
from datetime import datetime
import uuid

agent_bp = Blueprint('agent', __name__)


def generate_batch_code():
    """Generate unique batch code."""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
    unique = str(uuid.uuid4())[:6].upper()
    return f'RM-{timestamp}-{unique}'


def generate_batch_number():
    """Generate unique batch number."""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
    unique = str(uuid.uuid4())[:6].upper()
    return f'BATCH-{timestamp}-{unique}'


@agent_bp.route('/dashboard')
@login_required
@role_required('agent')
def dashboard():
    # Agent-specific stats
    my_materials = RawMaterial.query.filter_by(submitted_by=current_user.id)
    total_submitted = my_materials.count()
    pending_count = my_materials.filter_by(status='pending').count()
    in_process_count = my_materials.filter_by(status='in_process').count()
    completed_count = my_materials.filter_by(status='completed').count()

    # Recent submissions
    recent_materials = my_materials.order_by(RawMaterial.created_at.desc()).limit(5).all()

    # Recent batches from my materials
    my_material_ids = [m.id for m in my_materials.all()]
    recent_batches = Batch.query.filter(
        Batch.raw_material_id.in_(my_material_ids)
    ).order_by(Batch.created_at.desc()).limit(5).all()

    # Yield comparison data
    yield_data = db.session.query(
        RawMaterial.batch_code,
        YieldPrediction.predicted_yield,
        Batch.actual_yield_percent
    ).join(YieldPrediction, YieldPrediction.raw_material_id == RawMaterial.id, isouter=True
    ).join(Batch, Batch.raw_material_id == RawMaterial.id, isouter=True
    ).filter(
        RawMaterial.submitted_by == current_user.id
    ).order_by(RawMaterial.created_at.desc()).limit(10).all()

    return render_template('agent/dashboard.html',
                           total_submitted=total_submitted,
                           pending_count=pending_count,
                           in_process_count=in_process_count,
                           completed_count=completed_count,
                           recent_materials=recent_materials,
                           recent_batches=recent_batches,
                           yield_data=yield_data)


@agent_bp.route('/submit-batch', methods=['GET', 'POST'])
@login_required
@role_required('agent')
def submit_batch():
    prediction_result = None

    if request.method == 'POST':
        action = request.form.get('action', 'submit')

        # Get form data
        material_type = request.form.get('material_type')
        weight_kg = request.form.get('weight_kg')
        grade = request.form.get('grade', '')
        source = request.form.get('source', '')
        supplier = request.form.get('supplier', '')
        silica_percent = request.form.get('silica_percent')
        iron_oxide_percent = request.form.get('iron_oxide_percent')
        alumina_percent = request.form.get('alumina_percent')
        moisture_content = request.form.get('moisture_content')
        received_date = request.form.get('received_date')
        notes = request.form.get('notes', '')

        # Validate
        errors = []
        try:
            weight_kg = float(weight_kg)
            silica_percent = float(silica_percent)
            iron_oxide_percent = float(iron_oxide_percent)
            alumina_percent = float(alumina_percent)
            moisture_content = float(moisture_content)

            total_percent = silica_percent + iron_oxide_percent + alumina_percent + moisture_content
            if total_percent > 100:
                errors.append(f'Total composition ({total_percent:.1f}%) cannot exceed 100%.')
            if weight_kg <= 0:
                errors.append('Weight must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Please enter valid numeric values for composition fields.')

        if not material_type:
            errors.append('Material type is required.')
        if not source:
            errors.append('Source is required.')
        if not received_date:
            errors.append('Received date is required.')

        if action == 'predict' and not errors:
            # Just show prediction, don't save
            prediction_result = predict_yield(
                silica_percent, iron_oxide_percent, alumina_percent, moisture_content
            )
            return render_template('agent/submit_batch.html',
                                   prediction_result=prediction_result,
                                   form_data=request.form)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('agent/submit_batch.html', form_data=request.form)

        # Get prediction
        prediction = predict_yield(
            silica_percent, iron_oxide_percent, alumina_percent, moisture_content
        )

        # Create raw material record
        batch_code = generate_batch_code()
        raw_material = RawMaterial(
            batch_code=batch_code,
            material_type=material_type,
            weight_kg=weight_kg,
            grade=grade,
            source=source,
            supplier=supplier,
            silica_percent=silica_percent,
            iron_oxide_percent=iron_oxide_percent,
            alumina_percent=alumina_percent,
            moisture_content=moisture_content,
            received_date=datetime.strptime(received_date, '%Y-%m-%d').date(),
            submitted_by=current_user.id,
            notes=notes,
            status='pending'
        )
        db.session.add(raw_material)
        db.session.flush()  # Get ID

        # Save prediction
        yield_pred = YieldPrediction(
            raw_material_id=raw_material.id,
            silica_percent=silica_percent,
            iron_oxide_percent=iron_oxide_percent,
            alumina_percent=alumina_percent,
            moisture_content=moisture_content,
            predicted_yield=prediction['predicted_yield'],
            confidence_score=prediction['confidence_score'],
            efficiency_rating=prediction['efficiency_rating']
        )
        db.session.add(yield_pred)

        # Create batch
        batch = Batch(
            batch_number=generate_batch_number(),
            raw_material_id=raw_material.id,
            total_input_weight=weight_kg,
            predicted_yield_percent=prediction['predicted_yield'],
            status='pending'
        )
        db.session.add(batch)
        db.session.flush()

        # Create Bayer process steps
        steps = [
            ('digestion', 1),
            ('clarification', 2),
            ('precipitation', 3),
            ('calcination', 4)
        ]
        for step_name, order in steps:
            step = BayerProcessLog(
                batch_id=batch.id,
                step=step_name,
                step_order=order,
                status='pending'
            )
            db.session.add(step)

        db.session.commit()

        flash(f'Batch {batch_code} submitted successfully! Predicted yield: {prediction["predicted_yield"]}%',
              'success')
        return redirect(url_for('agent.batch_detail', batch_id=batch.id))

    return render_template('agent/submit_batch.html', prediction_result=prediction_result)


@agent_bp.route('/batch/<int:batch_id>')
@login_required
@role_required('agent')
def batch_detail(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    # Ensure agent can only see their own batches
    if batch.raw_material.submitted_by != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('agent.dashboard'))

    process_steps = batch.process_logs.order_by(BayerProcessLog.step_order).all()
    byproducts = batch.byproducts.all()
    prediction = batch.raw_material.yield_predictions.first()

    return render_template('agent/batch_detail.html',
                           batch=batch,
                           process_steps=process_steps,
                           byproducts=byproducts,
                           prediction=prediction)


@agent_bp.route('/history')
@login_required
@role_required('agent')
def history():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    query = RawMaterial.query.filter_by(submitted_by=current_user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    materials = query.order_by(RawMaterial.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('agent/history.html',
                           materials=materials,
                           status_filter=status_filter)


@agent_bp.route('/update-process-step/<int:step_id>', methods=['POST'])
@login_required
@role_required('agent')
def update_process_step(step_id):
    step = BayerProcessLog.query.get_or_404(step_id)
    batch = step.batch

    # Verify ownership
    if batch.raw_material.submitted_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    step.status = request.form.get('status', step.status)
    step.temperature_celsius = request.form.get('temperature') or step.temperature_celsius
    step.pressure_bar = request.form.get('pressure') or step.pressure_bar
    step.duration_minutes = request.form.get('duration') or step.duration_minutes
    step.observations = request.form.get('observations', step.observations)
    step.operator_id = current_user.id

    if step.status == 'in_progress' and not step.started_at:
        step.started_at = datetime.utcnow()
    elif step.status == 'completed':
        step.completed_at = datetime.utcnow()
        step.output_weight = request.form.get('output_weight') or step.output_weight

        # Update batch status to next step
        step_progression = {
            'digestion': 'clarification',
            'clarification': 'precipitation',
            'precipitation': 'calcination',
            'calcination': 'completed'
        }
        next_status = step_progression.get(step.step)
        if next_status:
            batch.status = next_status
            if next_status == 'completed':
                batch.end_date = datetime.utcnow()
                batch.raw_material.status = 'completed'
                # Calculate actual yield
                if step.output_weight and batch.total_input_weight:
                    batch.total_output_weight = float(step.output_weight)
                    batch.actual_yield_percent = (
                        float(step.output_weight) / float(batch.total_input_weight) * 100
                    )
                # Auto-create byproduct entry
                _create_byproduct_entry(batch)
            else:
                batch.raw_material.status = 'in_process'
                if not batch.start_date:
                    batch.start_date = datetime.utcnow()

    db.session.commit()
    flash(f'Process step "{step.step}" updated successfully.', 'success')
    return redirect(url_for('agent.batch_detail', batch_id=batch.id))


def _create_byproduct_entry(batch):
    """Auto-create byproduct entry when batch completes."""
    raw = batch.raw_material
    # Estimate red mud quantity (typically 1-2.5x input weight)
    red_mud_qty = float(raw.weight_kg) * 1.5

    recommendation = recommend_byproduct_use(
        'red_mud',
        iron_oxide_percent=float(raw.iron_oxide_percent),
        alumina_percent=float(raw.alumina_percent),
        silica_percent=float(raw.silica_percent)
    )

    byproduct = Byproduct(
        batch_id=batch.id,
        byproduct_type='red_mud',
        quantity_kg=red_mud_qty,
        iron_oxide_percent=raw.iron_oxide_percent,
        alumina_percent=raw.alumina_percent,
        silica_percent=raw.silica_percent,
        recommended_use=recommendation['recommendation'],
        recommendation_confidence=recommendation['confidence'],
        status='pending'
    )
    db.session.add(byproduct)
