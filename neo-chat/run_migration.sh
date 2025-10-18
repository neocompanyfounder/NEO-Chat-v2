#!/bin/bash

# Run database migration 005
# This adds the 'name' column to the users table

# Database connection string
DB_URL="${DATABASE_URL:-postgres://postgres:ESlMOrLQzt7ovJ3f8vzW4yZ432F83qjRR3h38gUkR3YoF19m5TFnwWI3ZRYMEZQg@rg8kcssoscggosgkwg44w40c:5432/postgres}"

echo "Running migration 005: Add name column to users table..."

# Run the migration
psql "$DB_URL" -f src/db/migrations/005_add_user_name_column.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi
