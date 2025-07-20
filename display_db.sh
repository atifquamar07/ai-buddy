#!/bin/bash

# Check if user_id is provided
if [ $# -eq 0 ]; then
    echo "Please provide a user_id as an argument."
    exit 1
fi

USER_ID=$1
DB_NAME="nova_db"
DB_USER="nishant"
DB_PASS="nova123456"
DB_HOST="localhost"
DB_PORT="5432"

# Function to display table contents
display_tables() {
    clear
    echo "=== Conversation Table ==="
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT role, message, timestamp FROM conversation WHERE user_id = '$USER_ID' ORDER BY timestamp DESC LIMIT 5;"
    echo -e "\n=== Memory Table ==="
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT memory FROM memory WHERE user_id = '$USER_ID';"
    echo -e "\n=== Summary Table ==="
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT summary FROM summary WHERE user_id = '$USER_ID';"
}

# Main loop
while true; do
    display_tables
    sleep 5  # Refresh every 5 seconds
done