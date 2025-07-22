-- Create applicant_counts table
CREATE TABLE applicant_counts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scraper_id TEXT NOT NULL,
    name TEXT NOT NULL,
    count INTEGER,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    error TEXT,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- Create scrapers_config table
CREATE TABLE scrapers_config (
    scraper_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_applicant_counts_date ON applicant_counts(date);
CREATE INDEX idx_applicant_counts_scraper ON applicant_counts(scraper_id);
CREATE INDEX idx_applicant_counts_sync ON applicant_counts(synced_to_sheets);