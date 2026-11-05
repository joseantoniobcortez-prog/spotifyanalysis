-- ============================================================
-- Spotify Listening Analysis: database schema
-- Run this in the Supabase SQL Editor.
-- ============================================================


-- ------------------------------------------------------------
-- Raw table for plays collected by the scheduled API job.
-- Stores the full API response as JSON so no data is lost.
-- ------------------------------------------------------------
create table if not exists raw_plays (
    played_at   timestamptz not null,               -- play time, UTC
    track_uri   text        not null,               -- spotify:track:xxxx
    payload     jsonb       not null,               -- full API record
    ingested_at timestamptz not null default now(), -- when it was saved
    primary key (played_at, track_uri)              -- blocks duplicates
);


-- ------------------------------------------------------------
-- Raw table for the Extended Streaming History export.
-- Keeps every play, including skips, for later analysis.
-- ------------------------------------------------------------
create table if not exists raw_streaming_history (
    played_at    timestamptz not null,  -- play time, UTC
    track_uri    text        not null,  -- spotify:track:xxxx
    track_name   text,
    artist_name  text,
    album_name   text,
    ms_played    int         not null,  -- milliseconds actually listened
    platform     text,
    reason_start text,
    reason_end   text,
    shuffle      boolean,
    skipped      boolean,
    primary key (played_at, track_uri)  -- blocks duplicates
);


-- Block access through Supabase's public API.
-- Scripts and Power BI connect as the database owner and are unaffected.
alter table raw_plays enable row level security;
alter table raw_streaming_history enable row level security;


-- ------------------------------------------------------------
-- Cleaned view that Power BI reads from.
-- Merges both sources without double counting.
-- ------------------------------------------------------------
drop view if exists plays_clean;

create view plays_clean with (security_invoker = true) as

-- Part 1: API plays, only after the export ends
select
    played_at,
    played_at at time zone 'Asia/Manila'     as played_at_manila,
    payload->'track'->>'id'                  as track_id,
    payload->'track'->>'name'                as track_name,
    payload->'track'->'artists'->0->>'name'  as artist_name,
    payload->'track'->'album'->>'name'       as album_name,
    (payload->'track'->>'duration_ms')::int  as duration_ms,
    null::int                                as ms_played,  -- API doesn't provide it
    'api'                                    as source
from raw_plays
where played_at > (select max(played_at) from raw_streaming_history)

union all

-- Part 2: export plays of 30 seconds or more
-- (matches how Spotify counts a stream)
select
    played_at,
    played_at at time zone 'Asia/Manila',
    split_part(track_uri, ':', 3),           -- "spotify:track:abc" -> "abc"
    track_name,
    artist_name,
    album_name,
    null::int,                               -- export has no full track length
    ms_played,
    'export'
from raw_streaming_history
where ms_played >= 30000;