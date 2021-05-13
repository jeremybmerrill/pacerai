CREATE TABLE rss_docket_entries (
    title text,
    case_number text,
    case_name text,
    docket_id integer,
    description text,
    document_type text,
    guid text,
    pub_date timestamptz,
    scrape_date timestamptz,
    docket_entry_seq_num integer,
    docket_entry_num integer,
    court text,
    UNIQUE (case_number, pub_date)
);
