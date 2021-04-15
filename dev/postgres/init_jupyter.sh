
#!/bin/bash

set -e
set -u

function create_user_and_database() {
	local database=$1
	echo "  Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		CREATE USER $database;
		CREATE DATABASE $database;
		GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	CREATE SEQUENCE IF NOT EXISTS users_info_id_seq;

	-- Table Definition
	CREATE TABLE "public"."users_info" (
		"id" int4 NOT NULL DEFAULT nextval('users_info_id_seq'::regclass),
		"username" varchar NOT NULL,
		"password" bytea NOT NULL,
		"is_authorized" bool,
		"email" varchar,
		PRIMARY KEY ("id")
	);

	INSERT INTO "public"."users_info" ("id", "username", "password", "is_authorized", "email") VALUES
	(2, 'bob@cashstory.com', '\x24326224313224416a74734e53525a4a6e6e2f2e49555250494244454f6d4e4d3664657078314661347166704b734447495238583444684e5549372e', 't', NULL);
EOSQL
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	CREATE SEQUENCE IF NOT EXISTS users_id_seq;

	-- Table Definition
	CREATE TABLE "public"."users" (
		"id" int4 NOT NULL DEFAULT nextval('users_id_seq'::regclass),
		"name" varchar(255),
		"admin" bool,
		"created" timestamp,
		"last_activity" timestamp,
		"cookie_id" varchar(255) NOT NULL,
		"state" text,
		"encrypted_auth_state" bytea,
		PRIMARY KEY ("id")
	);

	INSERT INTO "public"."users" ("id", "name", "admin", "created", "last_activity", "cookie_id", "state", "encrypted_auth_state") VALUES
	(2, 'bob@cashstory.com', 't', '2020-04-18 09:02:47.941605', '2021-04-15 14:04:55.417564', '2c74e5d1668347b2b016229bf8c23463', '{}', NULL);

EOSQL
}

create_user_and_database $JUPYTER_DB
echo "Jupyterdb created"
