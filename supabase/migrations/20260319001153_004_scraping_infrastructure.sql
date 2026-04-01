-- ============================================
-- 004: Scraping Infrastructure
-- ============================================

-- Prompt Templates: per-state AI agent brain (versioned)
-- Created BEFORE source_catalog due to FK dependency
CREATE TABLE prompt_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    state           CHAR(2) NOT NULL,
    source_type     TEXT NOT NULL CHECK (source_type IN (
                        'stocking', 'regulations', 'conditions', 'reports', 'ice'
                    )),
    version         INT NOT NULL DEFAULT 1,
    system_prompt   TEXT NOT NULL,
    schema_json     JSONB NOT NULL,
    examples        JSONB,
    species_map     JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    accuracy_score  FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_state ON prompt_templates(state, source_type);
CREATE UNIQUE INDEX idx_prompt_active ON prompt_templates(state, source_type) WHERE is_active = true;

-- Source Catalog: master list of all scraping targets
CREATE TABLE source_catalog (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state                   CHAR(2) NOT NULL,
    name                    TEXT NOT NULL,
    url                     TEXT NOT NULL,
    source_type             TEXT NOT NULL CHECK (source_type IN (
                                'stocking', 'regulations', 'conditions', 'reports', 'ice'
                            )),
    format                  TEXT NOT NULL CHECK (format IN (
                                'html_table', 'html_list', 'pdf', 'csv', 'api', 'json'
                            )),
    scrape_frequency_hours  INT NOT NULL DEFAULT 6,
    prompt_template_id      UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    js_rendered             BOOLEAN NOT NULL DEFAULT false,
    status                  TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
                                'active', 'paused', 'broken', 'needs_review', 'retired'
                            )),
    consecutive_failures    INT NOT NULL DEFAULT 0,
    last_scraped_at         TIMESTAMPTZ,
    last_success_at         TIMESTAMPTZ,
    config                  JSONB NOT NULL DEFAULT '{}',
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_source_state ON source_catalog(state);
CREATE INDEX idx_source_status ON source_catalog(status);
CREATE INDEX idx_source_type ON source_catalog(source_type);

-- Scrape Logs: full audit trail for every scrape run
CREATE TABLE scrape_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id           UUID NOT NULL REFERENCES source_catalog(id) ON DELETE CASCADE,
    prompt_template_id  UUID REFERENCES prompt_templates(id),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    http_status         INT,
    response_size_bytes INT,
    records_extracted   INT NOT NULL DEFAULT 0,
    records_stored      INT NOT NULL DEFAULT 0,
    records_duplicated  INT NOT NULL DEFAULT 0,
    records_unmatched   INT NOT NULL DEFAULT 0,
    confidence_avg      FLOAT,
    unmatched_names     JSONB,
    errors              JSONB,
    raw_snapshot_url    TEXT,
    status              TEXT NOT NULL DEFAULT 'running' CHECK (status IN (
                            'running', 'success', 'partial', 'failed'
                        )),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scrape_source ON scrape_logs(source_id, started_at DESC);
CREATE INDEX idx_scrape_status ON scrape_logs(status);
CREATE INDEX idx_scrape_unmatched ON scrape_logs(records_unmatched) WHERE records_unmatched > 0;

-- Now add the FK from stocking_events to scrape_logs
ALTER TABLE stocking_events
    ADD CONSTRAINT fk_stocking_scrape_log
    FOREIGN KEY (scrape_log_id) REFERENCES scrape_logs(id) ON DELETE SET NULL;
