-- PostgreSQL initialization script
-- This script will create the necessary extensions, triggers, and indexes for the apartment rental app

-- Create the database if it doesn't exist
CREATE DATABASE fastapi_apartments;

\c fastapi_apartments;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- For text similarity search
CREATE EXTENSION IF NOT EXISTS unaccent;    -- For accent-insensitive search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- For UUID generation

-- Create the automatic timestamp update function
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Create the search_vector update function for full-text search
CREATE OR REPLACE FUNCTION apartments_search_vector_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- NOTE: The tables will be created by SQLAlchemy when the application starts
-- This script just sets up the PostgreSQL environment 