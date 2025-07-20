#!/bin/bash

# Path to your project directory
PROJECT_DIR="/hci-buddy"

# Path to your virtual environment
VENV_PATH="$PROJECT_DIR/venv"

# Path to your Gunicorn config file
GUNICORN_CONF="$PROJECT_DIR/gunicorn.conf.py"

# Path to your FastAPI application
APP_PATH="app:app"

# PID file path (should match the one in your Gunicorn config)
PID_FILE="$PROJECT_DIR/logs/nova.pid"

# Log directory
LOG_DIR="$PROJECT_DIR/logs"

# Temporary directory
TMP_DIR="$PROJECT_DIR/tmp"

# Function to activate virtual environment
activate_venv() {
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
}

# Function to create temporary directory
create_tmp_dir() {
    if [ ! -d "$TMP_DIR" ]; then
        echo "Creating temporary directory..."
        mkdir -p "$TMP_DIR"
        chmod 755 "$TMP_DIR"
    fi
}

# Function to create log directory
create_log_dir() {
    if [ ! -d "$LOG_DIR" ]; then
        echo "Creating log directory..."
        mkdir -p "$LOG_DIR"
        chmod 755 "$LOG_DIR"
    fi
}

# Start the Gunicorn server
start() {
    if [ -f "$PID_FILE" ]; then
        echo "Server is already running."
        exit 1
    fi
    
    echo "Starting Gunicorn server..."
    activate_venv
    create_log_dir
    create_tmp_dir
   cd "$PROJECT_DIR"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    gunicorn -c "$GUNICORN_CONF" "$APP_PATH"
    if [ $? -eq 0 ]; then
        echo "Server started successfully."
    else
        echo "Failed to start server. Check logs for details."
    fi
}

# Stop the Gunicorn server gracefully
stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Server is not running."
        exit 1
    fi
    
    echo "Stopping Gunicorn server..."
    kill -TERM $(cat "$PID_FILE")
    rm -f "$PID_FILE"
    echo "Server stopped."
}

# Kill the Gunicorn server forcefully
kill_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Server is not running."
        exit 1
    fi
    
    echo "Forcefully killing Gunicorn server..."
    kill -9 $(cat "$PID_FILE")
    rm -f "$PID_FILE"
    echo "Server killed."
}
# Check the status of the Gunicorn server
status() {
    if [ -f "$PID_FILE" ]; then
        echo "Server is running. PID: $(cat "$PID_FILE")"
    else
        echo "Server is not running."
    fi
}

# Restart the Gunicorn server
restart() {
    echo "Restarting Gunicorn server..."
    stop
    sleep 2
    start
}

# Main script logic
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    kill)
        kill_server
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|kill|restart|status}"
        exit 1
        ;;
esac

exit 0