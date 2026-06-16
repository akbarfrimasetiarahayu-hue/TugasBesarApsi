-- ============================================================
-- FILE: migrations/001_create_tables_postgres.sql
-- Sistem Penilaian 360° Core Values AKHLAK
-- PT. Energi Nusantara
-- ============================================================

-- TABLE: roles
CREATE TABLE IF NOT EXISTS roles (
    id_role     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name   VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

-- TABLE: employees
CREATE TABLE IF NOT EXISTS employees (
    user_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_supervisor INTEGER NULL,
    nama        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    nip         VARCHAR(20) UNIQUE NOT NULL,
    position    VARCHAR(100),
    division    VARCHAR(100),
    FOREIGN KEY (id_supervisor) REFERENCES employees(user_id)
);

-- TABLE: user_accounts
CREATE TABLE IF NOT EXISTS user_accounts (
    id_account  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_employee INTEGER NOT NULL,
    id_role     INTEGER NOT NULL,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    status      VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (id_employee) REFERENCES employees(user_id),
    FOREIGN KEY (id_role) REFERENCES roles(id_role)
);

-- TABLE: assessment_periods
CREATE TABLE IF NOT EXISTS assessment_periods (
    id_period   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_name VARCHAR(100) NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    status      VARCHAR(20) DEFAULT 'draft'
);

-- TABLE: indikators
CREATE TABLE IF NOT EXISTS indikators (
    id_indikator    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    core_value      INTEGER NOT NULL,
    indikator_name  VARCHAR(255) NOT NULL,
    nilai_min       INTEGER DEFAULT 1,
    nilai_max       INTEGER DEFAULT 5
);

-- TABLE: penilaians
CREATE TABLE IF NOT EXISTS penilaians (
    id_penilaian    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_period       INTEGER NOT NULL,
    id_evaluator    INTEGER NOT NULL,
    id_karyawan     INTEGER NOT NULL,
    jenis_penilaian VARCHAR(20) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    submitted_at    TIMESTAMP NULL,
    FOREIGN KEY (id_period) REFERENCES assessment_periods(id_period),
    FOREIGN KEY (id_evaluator) REFERENCES employees(user_id),
    FOREIGN KEY (id_karyawan) REFERENCES employees(user_id)
);

-- TABLE: detail_penilaians
CREATE TABLE IF NOT EXISTS detail_penilaians (
    id_detail       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    penilaian_id    INTEGER NOT NULL,
    id_indikator    INTEGER NOT NULL,
    score           INTEGER NOT NULL,
    feedback        TEXT NULL,
    FOREIGN KEY (penilaian_id) REFERENCES penilaians(id_penilaian),
    FOREIGN KEY (id_indikator) REFERENCES indikators(id_indikator)
);

-- TABLE: hasil_akhirs
CREATE TABLE IF NOT EXISTS hasil_akhirs (
    id_result       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_employee     INTEGER NOT NULL,
    id_period       INTEGER NOT NULL,
    score_atasan    REAL NULL,
    score_bawahan   REAL NULL,
    score_rekan     REAL NULL,
    score_self      REAL NULL,
    total_score     REAL NULL,
    category        VARCHAR(50) NULL,
    calculated_at   TIMESTAMP NULL,
    FOREIGN KEY (id_employee) REFERENCES employees(user_id),
    FOREIGN KEY (id_period) REFERENCES assessment_periods(id_period)
);

-- TABLE: hasil_reports
CREATE TABLE IF NOT EXISTS hasil_reports (
    id_report       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_period       INTEGER NOT NULL,
    report_type     VARCHAR(50),
    generate_date   DATE,
    generated_by    INTEGER,
    file_path       VARCHAR(255),
    FOREIGN KEY (id_period) REFERENCES assessment_periods(id_period),
    FOREIGN KEY (generated_by) REFERENCES employees(user_id)
);
