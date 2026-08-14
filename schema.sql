-- Create database
CREATE DATABASE IF NOT EXISTS saeros_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE saeros_db;

-- TABLE: roles

CREATE TABLE IF NOT EXISTS roles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: users

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    role_id       INT          NOT NULL,
    is_approved   TINYINT(1)   DEFAULT 0,
    is_active     TINYINT(1)   DEFAULT 1,
    is_admin      TINYINT(1)   DEFAULT 0,
    phone         VARCHAR(20),
    department    VARCHAR(100),
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login    TIMESTAMP    NULL,
    approved_by   INT          NULL,
    approved_at   TIMESTAMP    NULL,
    FOREIGN KEY (role_id)    REFERENCES roles(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);


-- TABLE: raw_materials

CREATE TABLE IF NOT EXISTS raw_materials (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    batch_code          VARCHAR(50)  NOT NULL UNIQUE,
    material_type       ENUM('bauxite', 'aluminum_scrap', 'mixed') NOT NULL,
    weight_kg           DECIMAL(10,2) NOT NULL,
    grade               VARCHAR(50),
    source              VARCHAR(200) NOT NULL,
    supplier            VARCHAR(200),
    silica_percent      DECIMAL(5,2)  NOT NULL COMMENT 'SiO2 %',
    iron_oxide_percent  DECIMAL(5,2)  NOT NULL COMMENT 'Fe2O3 %',
    alumina_percent     DECIMAL(5,2)  NOT NULL COMMENT 'Al2O3 %',
    moisture_content    DECIMAL(5,2)  NOT NULL COMMENT 'Moisture %',
    other_minerals      TEXT          COMMENT 'JSON of other mineral percentages',
    received_date       DATE          NOT NULL,
    submitted_by        INT           NOT NULL,
    status              ENUM('pending', 'in_process', 'completed', 'rejected') DEFAULT 'pending',
    notes               TEXT,
    created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (submitted_by) REFERENCES users(id)
);


-- TABLE: batches

CREATE TABLE IF NOT EXISTS batches (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    batch_number          VARCHAR(50) NOT NULL UNIQUE,
    raw_material_id       INT         NOT NULL,
    status                ENUM('pending','digestion','clarification','precipitation','calcination','completed','failed') DEFAULT 'pending',
    start_date            TIMESTAMP   NULL,
    end_date              TIMESTAMP   NULL,
    assigned_operator     INT         NULL,
    total_input_weight    DECIMAL(10,2),
    total_output_weight   DECIMAL(10,2),
    actual_yield_percent  DECIMAL(5,2),
    predicted_yield_percent DECIMAL(5,2),
    efficiency_rating     DECIMAL(5,2),
    notes                 TEXT,
    created_at            TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_material_id)   REFERENCES raw_materials(id),
    FOREIGN KEY (assigned_operator) REFERENCES users(id)
);
-- TABLE: bayer_process_log

CREATE TABLE IF NOT EXISTS bayer_process_log (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    batch_id            INT  NOT NULL,
    step                ENUM('digestion','clarification','precipitation','calcination') NOT NULL,
    step_order          INT  NOT NULL,
    status              ENUM('pending','in_progress','completed','failed') DEFAULT 'pending',
    temperature_celsius DECIMAL(6,2),
    pressure_bar        DECIMAL(6,2),
    duration_minutes    INT,
    operator_id         INT,
    input_weight        DECIMAL(10,2),
    output_weight       DECIMAL(10,2),
    chemical_additions  TEXT COMMENT 'JSON of chemicals added',
    observations        TEXT,
    started_at          TIMESTAMP NULL,
    completed_at        TIMESTAMP NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id)    REFERENCES batches(id),
    FOREIGN KEY (operator_id) REFERENCES users(id)
);
-- TABLE: byproducts

CREATE TABLE IF NOT EXISTS byproducts (
    id                        INT AUTO_INCREMENT PRIMARY KEY,
    batch_id                  INT          NOT NULL,
    byproduct_type            ENUM('red_mud','manganese_alloy','silica_residue','other') NOT NULL,
    quantity_kg               DECIMAL(10,2) NOT NULL,
    iron_oxide_percent        DECIMAL(5,2),
    alumina_percent           DECIMAL(5,2),
    silica_percent            DECIMAL(5,2),
    manganese_percent         DECIMAL(5,2),
    rare_earth_percent        DECIMAL(5,2),
    other_composition         TEXT          COMMENT 'JSON of other composition data',
    recommended_use           ENUM('cement_additive','iron_recovery','rare_earth_extraction','road_construction','soil_amendment','further_processing','disposal') NULL,
    recommendation_confidence DECIMAL(5,2),
    assigned_to               INT           NULL COMMENT 'Scrap team user ID',
    status                    ENUM('pending','assigned','in_treatment','completed','disposed') DEFAULT 'pending',
    treatment_result          TEXT,
    secondary_output_kg       DECIMAL(10,2),
    treatment_completed_at    TIMESTAMP     NULL,
    created_at                TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at                TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id)   REFERENCES batches(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);
-- TABLE: yield_predictions

CREATE TABLE IF NOT EXISTS yield_predictions (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    raw_material_id    INT          NOT NULL,
    silica_percent     DECIMAL(5,2) NOT NULL,
    iron_oxide_percent DECIMAL(5,2) NOT NULL,
    alumina_percent    DECIMAL(5,2) NOT NULL,
    moisture_content   DECIMAL(5,2) NOT NULL,
    predicted_yield    DECIMAL(5,2) NOT NULL,
    confidence_score   DECIMAL(5,2),
    efficiency_rating  VARCHAR(20),
    model_version      VARCHAR(20)  DEFAULT '1.0',
    created_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id)
);

-- TABLE: admin_logs

CREATE TABLE IF NOT EXISTS admin_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    admin_id    INT          NOT NULL,
    action      VARCHAR(100) NOT NULL,
    target_type VARCHAR(50)  COMMENT 'user, batch, byproduct, etc.',
    target_id   INT,
    details     TEXT,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id)
);

-- INDEXES (for query performance)

CREATE INDEX idx_raw_materials_status       ON raw_materials(status);
CREATE INDEX idx_raw_materials_submitted_by ON raw_materials(submitted_by);
CREATE INDEX idx_batches_status             ON batches(status);
CREATE INDEX idx_batches_raw_material       ON batches(raw_material_id);
CREATE INDEX idx_bayer_log_batch            ON bayer_process_log(batch_id);
CREATE INDEX idx_byproducts_batch           ON byproducts(batch_id);
CREATE INDEX idx_byproducts_assigned        ON byproducts(assigned_to);
CREATE INDEX idx_byproducts_status          ON byproducts(status);
CREATE INDEX idx_yield_predictions_material ON yield_predictions(raw_material_id);
CREATE INDEX idx_admin_logs_admin           ON admin_logs(admin_id);
CREATE INDEX idx_admin_logs_created         ON admin_logs(created_at);

-- SEED DATA: Default roles
INSERT INTO roles (name, description) VALUES
    ('admin',      'System administrator with full access'),
    ('agent',      'Field agent who submits raw material batches'),
    ('scrap_team', 'Scrap processing team handling by-products')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- SEED DATA: Default admin user
-- Username : admin
-- Password : admin123  (bcrypt hashed)
INSERT INTO users (
    username, email, password_hash, full_name,
    role_id, is_approved, is_active, is_admin, department
) VALUES (
    'admin',
    'admin@saeros.com',
    '$2b$12$Zm48RntQ1DKUFSviy4h4QuLzsyYesgiqZUgEOHRoBDHtft/1HONYW',
    'System Administrator',
    1, 1, 1, 1,
    'IT Administration'
) ON DUPLICATE KEY UPDATE username = 'admin';

-- SEED DATA: Sample agent user
-- Username : agent1
-- Password : agent123
INSERT INTO users (
    username, email, password_hash, full_name,
    role_id, is_approved, is_active, is_admin, department
) VALUES (
    'agent1',
    'agent1@saeros.com',
    '$2b$12$aP2qu3raqDXxA66kpXWMmemqPr9exgnzU5Fr0OejhnVRgC9L8et.W',
    'John Smith',
    2, 1, 1, 0,
    'Field Operations'
) ON DUPLICATE KEY UPDATE username = 'agent1';

-- SEED DATA: Sample scrap team user
-- Username : scrap1
-- Password : scrap123
INSERT INTO users (
    username, email, password_hash, full_name,
    role_id, is_approved, is_active, is_admin, department
) VALUES (
    'scrap1',
    'scrap1@saeros.com',
    '$2b$12$eg4XOvKlfZv5ntiwNUHpr.JXchVljqKH82rN6M.sAeTfR3SnAiMn2',
    'Maria Garcia',
    3, 1, 1, 0,
    'Scrap Processing'
) ON DUPLICATE KEY UPDATE username = 'scrap1';! 

