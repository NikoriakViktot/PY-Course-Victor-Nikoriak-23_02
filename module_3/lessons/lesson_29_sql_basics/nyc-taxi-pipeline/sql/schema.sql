-- =============================================================================
-- NYC Taxi Analytics — PostgreSQL schema (aggregated data ONLY)
-- No raw trip rows. Every table is pre-aggregated before insert.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Zone reference (static lookup — loaded once from taxi_zones.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zones (
    zone_id    INT  PRIMARY KEY,
    zone_name  TEXT NOT NULL,
    borough    TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- 2. Core aggregated trips (the primary analytical table)
--    Granularity: year × month × pickup_zone × dropoff_zone
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips_agg (
    year           INT   NOT NULL,
    month          INT   NOT NULL,
    pu_location_id INT   NOT NULL REFERENCES zones(zone_id),
    do_location_id INT   NOT NULL REFERENCES zones(zone_id),
    trips_count    INT   NOT NULL,
    avg_fare       FLOAT NOT NULL,
    total_revenue  FLOAT NOT NULL,
    avg_distance   FLOAT NOT NULL,
    PRIMARY KEY (year, month, pu_location_id, do_location_id)
);

CREATE INDEX IF NOT EXISTS idx_trips_agg_year_month
    ON trips_agg (year, month);

CREATE INDEX IF NOT EXISTS idx_trips_agg_pu
    ON trips_agg (pu_location_id);

CREATE INDEX IF NOT EXISTS idx_trips_agg_do
    ON trips_agg (do_location_id);

-- ---------------------------------------------------------------------------
-- 3. Monthly summary (KPI dashboard — one row per month)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monthly_summary (
    year          INT    NOT NULL,
    month         INT    NOT NULL,
    total_trips   BIGINT NOT NULL,
    total_revenue FLOAT  NOT NULL,
    avg_fare      FLOAT  NOT NULL,
    avg_distance  FLOAT  NOT NULL,
    PRIMARY KEY (year, month)
);

-- ---------------------------------------------------------------------------
-- 4. Zone summary (heatmap + ranking — one row per zone per month)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zone_summary (
    zone_id       INT    NOT NULL REFERENCES zones(zone_id),
    year          INT    NOT NULL,
    month         INT    NOT NULL,
    pickup_trips  BIGINT NOT NULL DEFAULT 0,
    dropoff_trips BIGINT NOT NULL DEFAULT 0,
    revenue       FLOAT  NOT NULL DEFAULT 0,
    PRIMARY KEY (zone_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_zone_summary_year_month
    ON zone_summary (year, month);

-- ---------------------------------------------------------------------------
-- 5. Materialized view: all-time top routes (precomputed, refreshed by ETL)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS top_routes AS
SELECT
    pu_location_id,
    do_location_id,
    SUM(trips_count)     AS total_trips,
    AVG(avg_fare)        AS avg_fare,
    SUM(total_revenue)   AS total_revenue,
    AVG(avg_distance)    AS avg_distance
FROM trips_agg
GROUP BY pu_location_id, do_location_id
ORDER BY total_trips DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_top_routes_pk
    ON top_routes (pu_location_id, do_location_id);

