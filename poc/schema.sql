-- RDS Postgres (db.t4g.medium). One customer.

CREATE TABLE users (
    user_id     text PRIMARY KEY,        -- Cognito sub
    name        text,
    role        text NOT NULL            -- operator | team_lead
);

CREATE TABLE shipments (
    id                 serial PRIMARY KEY,
    container_no       text NOT NULL,
    booking_ref        text,
    owner_id           text REFERENCES users,
    carrier            text,
    vessel             text,
    pol                text,             -- port of loading
    pod                text,             -- port of discharge
    status             text,             -- at_origin | in_transit | arrived
    planned_arrival    timestamptz,
    estimated_arrival  timestamptz,
    customs_hold       boolean DEFAULT false,
    last_event         text,
    last_event_at      timestamptz,
    refreshed_at       timestamptz       -- set by the ingest job, every 4 hours
);

CREATE TABLE events (
    id           serial PRIMARY KEY,
    shipment_id  int REFERENCES shipments,
    event        text,
    location     text,
    event_at     timestamptz
);

CREATE TABLE answer_cache (
    key         text PRIMARY KEY,        -- sha1 of the normalised question
    answer      text,
    created_at  timestamptz DEFAULT now()
);

-- The question and tool-call logs live in CloudWatch; ../data/ has the pilot exports.
