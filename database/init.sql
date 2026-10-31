-- PostgreSQL schema + sample data. Import into an empty database.

BEGIN;


CREATE TABLE wanted_criminals (
	id SERIAL NOT NULL, 
	name VARCHAR(120), 
	nickname VARCHAR(120) NOT NULL, 
	reward NUMERIC(14, 2) NOT NULL, 
	last_known_location TEXT NOT NULL, 
	difficulty INTEGER NOT NULL, 
	armed BOOLEAN NOT NULL, 
	has_crew BOOLEAN NOT NULL, 
	escape_master BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT nonnegative_reward CHECK (reward >= 0), 
	CONSTRAINT valid_difficulty CHECK (difficulty BETWEEN 1 AND 10)
)

;


CREATE TABLE hunt_logs (
	id SERIAL NOT NULL, 
	criminal_id INTEGER NOT NULL, 
	success BOOLEAN NOT NULL, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(criminal_id) REFERENCES wanted_criminals (id)
)

;

CREATE INDEX ix_hunt_logs_criminal_id ON hunt_logs (criminal_id);

INSERT INTO wanted_criminals (id, name, nickname, reward, last_known_location, difficulty, armed, has_crew, escape_master) VALUES (1, 'Kael Voss', 'Void Viper', 15000, 'Europa, abandoned ice refinery', 8, true, true, true), (2, NULL, 'Ghost Comet', 8500, 'Asteroid belt, sector C-12', 7, false, false, true), (3, 'Rhea Draven', 'Red Nova', 25000, 'Mars, underground docks', 10, true, true, false), (4, 'Orin Vale', 'Scrap King', 3000, 'Titan, scrapyard settlement', 3, false, true, false), (5, NULL, 'Night Falcon', 12000, 'Ganymede, cargo terminal', 6, true, false, true);

SELECT setval(pg_get_serial_sequence('wanted_criminals', 'id'), (SELECT MAX(id) FROM wanted_criminals));

INSERT INTO hunt_logs (id, criminal_id, success, notes) VALUES (1, 1, false, 'Target escaped through an asteroid field.'), (2, 1, true, 'Captured at the refueling station.'), (3, 2, false, 'Decoy signal led to an empty ship.'), (4, 2, true, 'Target detained near the cargo terminal.'), (5, 3, false, 'Crew interference prevented capture.'), (6, 3, true, 'Captured after disabling the shuttle.'), (7, 4, false, 'Tracking beacon was discovered.'), (8, 4, true, 'Target surrendered at the checkpoint.'), (9, 5, false, 'Lost contact during a solar storm.'), (10, 5, true, 'Captured in an abandoned refinery.');

SELECT setval(pg_get_serial_sequence('hunt_logs', 'id'), (SELECT MAX(id) FROM hunt_logs));

COMMIT;
