CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    total_points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hidden_missions (
    id SERIAL PRIMARY KEY,
    week_id VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    mission_type VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    bonus_points INTEGER NOT NULL DEFAULT 0,
    predicted_overall_score DOUBLE PRECISION NULL,
    approve_probability DOUBLE PRECISION NULL,
    ai_model_version VARCHAR(50) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activity_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mission_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    ai_confidence DOUBLE PRECISION NULL,
    ai_probabilities JSONB NULL,
    ai_raw_result JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_images (
    id SERIAL PRIMARY KEY,
    verification_id INTEGER NOT NULL REFERENCES activity_verifications(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    public_url VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS point_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
