from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)

    # Relationships
    raw_materials = db.relationship('RawMaterial', backref='submitter', lazy='dynamic',
                                    foreign_keys='RawMaterial.submitted_by')
    assigned_byproducts = db.relationship('Byproduct', backref='assigned_user', lazy='dynamic',
                                          foreign_keys='Byproduct.assigned_to')
    admin_logs = db.relationship('AdminLog', backref='admin_user', lazy='dynamic',
                                 foreign_keys='AdminLog.admin_id')

    def get_role_name(self):
        return self.role.name if self.role else 'unknown'

    def is_role(self, role_name):
        return self.role.name == role_name if self.role else False

    def __repr__(self):
        return f'<User {self.username}>'


class RawMaterial(db.Model):
    __tablename__ = 'raw_materials'
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), nullable=False, unique=True)
    material_type = db.Column(db.Enum('bauxite', 'aluminum_scrap', 'mixed'), nullable=False)
    weight_kg = db.Column(db.Numeric(10, 2), nullable=False)
    grade = db.Column(db.String(50))
    source = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(200))
    silica_percent = db.Column(db.Numeric(5, 2), nullable=False)
    iron_oxide_percent = db.Column(db.Numeric(5, 2), nullable=False)
    alumina_percent = db.Column(db.Numeric(5, 2), nullable=False)
    moisture_content = db.Column(db.Numeric(5, 2), nullable=False)
    other_minerals = db.Column(db.Text)
    received_date = db.Column(db.Date, nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'in_process', 'completed', 'rejected'), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    batches = db.relationship('Batch', backref='raw_material', lazy='dynamic')
    yield_predictions = db.relationship('YieldPrediction', backref='raw_material', lazy='dynamic')

    def __repr__(self):
        return f'<RawMaterial {self.batch_code}>'


class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False, unique=True)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    status = db.Column(
        db.Enum('pending', 'digestion', 'clarification', 'precipitation', 'calcination', 'completed', 'failed'),
        default='pending'
    )
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    assigned_operator = db.Column(db.Integer, db.ForeignKey('users.id'))
    total_input_weight = db.Column(db.Numeric(10, 2))
    total_output_weight = db.Column(db.Numeric(10, 2))
    actual_yield_percent = db.Column(db.Numeric(5, 2))
    predicted_yield_percent = db.Column(db.Numeric(5, 2))
    efficiency_rating = db.Column(db.Numeric(5, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    process_logs = db.relationship('BayerProcessLog', backref='batch', lazy='dynamic',
                                   order_by='BayerProcessLog.step_order')
    byproducts = db.relationship('Byproduct', backref='batch', lazy='dynamic')

    def get_progress_percent(self):
        steps = {'pending': 0, 'digestion': 25, 'clarification': 50,
                 'precipitation': 75, 'calcination': 90, 'completed': 100, 'failed': 0}
        return steps.get(self.status, 0)

    def __repr__(self):
        return f'<Batch {self.batch_number}>'


class BayerProcessLog(db.Model):
    __tablename__ = 'bayer_process_log'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    step = db.Column(db.Enum('digestion', 'clarification', 'precipitation', 'calcination'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'failed'), default='pending')
    temperature_celsius = db.Column(db.Numeric(6, 2))
    pressure_bar = db.Column(db.Numeric(6, 2))
    duration_minutes = db.Column(db.Integer)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    input_weight = db.Column(db.Numeric(10, 2))
    output_weight = db.Column(db.Numeric(10, 2))
    chemical_additions = db.Column(db.Text)
    observations = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    operator = db.relationship('User', foreign_keys=[operator_id])

    def __repr__(self):
        return f'<BayerProcessLog {self.batch_id} - {self.step}>'


class Byproduct(db.Model):
    __tablename__ = 'byproducts'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    byproduct_type = db.Column(
        db.Enum('red_mud', 'manganese_alloy', 'silica_residue', 'other'), nullable=False
    )
    quantity_kg = db.Column(db.Numeric(10, 2), nullable=False)
    iron_oxide_percent = db.Column(db.Numeric(5, 2))
    alumina_percent = db.Column(db.Numeric(5, 2))
    silica_percent = db.Column(db.Numeric(5, 2))
    manganese_percent = db.Column(db.Numeric(5, 2))
    rare_earth_percent = db.Column(db.Numeric(5, 2))
    other_composition = db.Column(db.Text)
    recommended_use = db.Column(
        db.Enum('cement_additive', 'iron_recovery', 'rare_earth_extraction',
                'road_construction', 'soil_amendment', 'further_processing', 'disposal')
    )
    recommendation_confidence = db.Column(db.Numeric(5, 2))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(
        db.Enum('pending', 'assigned', 'in_treatment', 'completed', 'disposed'), default='pending'
    )
    treatment_result = db.Column(db.Text)
    secondary_output_kg = db.Column(db.Numeric(10, 2))
    treatment_completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_type_display(self):
        types = {
            'red_mud': 'Red Mud',
            'manganese_alloy': 'Manganese Alloy',
            'silica_residue': 'Silica Residue',
            'other': 'Other'
        }
        return types.get(self.byproduct_type, self.byproduct_type)

    def get_recommended_use_display(self):
        uses = {
            'cement_additive': 'Cement Additive',
            'iron_recovery': 'Iron Recovery',
            'rare_earth_extraction': 'Rare Earth Extraction',
            'road_construction': 'Road Construction',
            'soil_amendment': 'Soil Amendment',
            'further_processing': 'Further Processing',
            'disposal': 'Safe Disposal'
        }
        return uses.get(self.recommended_use, self.recommended_use or 'Not Assigned')

    def __repr__(self):
        return f'<Byproduct {self.byproduct_type} - Batch {self.batch_id}>'


class YieldPrediction(db.Model):
    __tablename__ = 'yield_predictions'
    id = db.Column(db.Integer, primary_key=True)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    silica_percent = db.Column(db.Numeric(5, 2), nullable=False)
    iron_oxide_percent = db.Column(db.Numeric(5, 2), nullable=False)
    alumina_percent = db.Column(db.Numeric(5, 2), nullable=False)
    moisture_content = db.Column(db.Numeric(5, 2), nullable=False)
    predicted_yield = db.Column(db.Numeric(5, 2), nullable=False)
    confidence_score = db.Column(db.Numeric(5, 2))
    efficiency_rating = db.Column(db.String(20))
    model_version = db.Column(db.String(20), default='1.0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<YieldPrediction {self.predicted_yield}%>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AdminLog {self.action}>'
