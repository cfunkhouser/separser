-- The GNU General Public License 3.0
--
-- stackexchange-schema.sql - Nov. 14, 2012 - Schema for separser.py
--
-- Copyright (C) 2012 Christian Funkhouser
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.
--
-- MySQL 5.0+
-- Create the tables to hold parsed Stack Exchange data

CREATE TABLE badges (
	id INT NOT NULL,
	user_id INT NOT NULL,
	name VARCHAR(255) NOT NULL,
	date DATETIME NOT NULL,
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

-- The TEXT here gives us 64k wiggle room. The next step is 16MB, and
-- I don't want to waste the space if not necessary. The space
-- requirement is a minimum of 1 byte extra for each entry, which
-- sounds trivial until you realize that we are dealing with 13
-- million records. If we have to, we can spare the 13MB, but let's
-- make sure we need it first.
CREATE TABLE comments (
	id INT NOT NULL,
	post_id INT NOT NULL,
	score SMALLINT NOT NULL DEFAULT 0,
	user_id INT NOT NULL,
	text TEXT NOT NULL DEFAULT "",
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE posthistory (
	id INT NOT NULL,
	post_history_type_id SMALLINT NOT NULL,
	post_id INT NOT NULL,
	revision_guid VARCHAR(37) NOT NULL,
	creation_date DATETIME NOT NULL,
	user_id INT NOT NULL,
	text TEXT NOT NULL DEFAULT "",
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE posts (
	id INT NOT NULL,
	post_type_id SMALLINT NOT NULL,
	accepted_answer_id INT NOT NULL,
	creation_date DATETIME NOT NULL,
	score SMALLINT NOT NULL DEFAULT 0,
	view_count INT NOT NULL DEFAULT 0,
	body MEDIUMTEXT NOT NULL DEFAULT "",
	owner_user_id INT NOT NULL,
	last_editor_user_id INT NOT NULL,
	last_editor_display_name VARCHAR(255) NOT NULL DEFAULT "",
	last_editor_date DATETIME NOT NULL,
	last_activity_date DATETIME NOT NULL,
	title VARCHAR(255) NOT NULL DEFAULT "",
	-- This should probably be a separate table, but we should think
	-- hard about how to do the extra parsing.
	tags TEXT NOT NULL,
	answer_count SMALLINT NOT NULL DEFAULT 0,
	comment_count SMALLINT NOT NULL DEFAULT 0,
	favorite_count SMALLINT NOT NULL DEFAULT 0,
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE users (
	id INT NOT NULL,
	reputation INT NOT NULL DEFAULT 0,
	creation_date DATETIME NOT NULL,
	display_name VARCHAR(255) NOT NULL,
	email_hash VARCHAR(32) NOT NULL DEFAULT "",
	last_access_date DATETIME,
	website_url VARCHAR(255) DEFAULT "",
	location TEXT, -- May be empty
	about_me TEXT, -- May be empty
	views SMALLINT NOT NULL DEFAULT 0,
	up_votes SMALLINT NOT NULL DEFAULT 0,
	down_votes SMALLINT NOT NULL DEFAULT 0,
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE votes (
	id INT NOT NULL,
	post_id INT NOT NULL,
	vote_type_id SMALLINT NOT NULL,
	creation_date DATETIME NOT NULL,
	PRIMARY KEY(id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;
