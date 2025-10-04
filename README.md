Here's a complete guide to run your Telegram AI tool in the background on Termux:
Method 1: Using nohup (Simple)
bash

# Run in background with nohup
nohup python telegram_ai_tagger.py > bot.log 2>&1 &

# Check if it's running
ps aux | grep python

# View logs
tail -f bot.log

# Stop the process
pkill -f "python telegram_ai_tagger.py"

Method 2: Using tmux (Recommended)
Install and setup tmux:
bash

pkg install tmux

Create a tmux session:
bash

# Create new session named "telegram-bot"
tmux new-session -d -s telegram-bot

# Attach to the session
tmux attach-session -t telegram-bot

# Now run your script inside tmux
python telegram_ai_tagger.py

To detach from tmux (keep running in background):
bash

# Press Ctrl+B, then D

Manage tmux sessions:
bash

# List all sessions
tmux list-sessions

# Reattach to session
tmux attach-session -t telegram-bot

# Kill session
tmux kill-session -t telegram-bot

Method 3: Using screen
bash

# Install screen
pkg install screen

# Create screen session
screen -S telegram-bot

# Run your script
python telegram_ai_tagger.py

# Detach from screen (keep running)
# Press Ctrl+A, then D

# List screen sessions
screen -ls

# Reattach to session
screen -r telegram-bot

# Kill screen session
screen -X -S telegram-bot quit

Method 4: Create a Startup Script
Create management script manage_bot.sh:
bash

#!/data/data/com.termux/files/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="telegram_ai_tagger.py"
LOG_FILE="$SCRIPT_DIR/bot.log"
PID_FILE="$SCRIPT_DIR/bot.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
            echo "Bot is already running (PID: $(cat "$PID_FILE"))"
        else
            echo "Starting Telegram AI Bot..."
            nohup python "$SCRIPT_DIR/$SCRIPT_NAME" > "$LOG_FILE" 2>&1 &
            echo $! > "$PID_FILE"
            echo "Bot started with PID: $!"
            echo "Logs: $LOG_FILE"
        fi
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null; then
                kill $PID
                echo "Bot stopped (PID: $PID)"
                rm -f "$PID_FILE"
            else
                echo "Bot is not running"
                rm -f "$PID_FILE"
            fi
        else
            echo "PID file not found. Is the bot running?"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null; then
                echo "Bot is running (PID: $PID)"
                echo "=== Recent Logs ==="
                tail -20 "$LOG_FILE"
            else
                echo "Bot is not running (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            echo "Bot is not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|logs}"
        exit 1
        ;;
esac

Make it executable and use it:
bash

chmod +x manage_bot.sh

# Start bot
./manage_bot.sh start

# Check status
./manage_bot.sh status

# View logs
./manage_bot.sh logs

# Stop bot
./manage_bot.sh stop

# Restart bot
./manage_bot.sh restart

Method 5: Auto-start on Termux Boot
Install Termux:Boot app:

    Install F-Droid from https://f-droid.org

    Install Termux:Boot from F-Droid

    Install Termux:API for additional features

Create boot script:
bash

# Create .termux/boot directory
mkdir -p ~/.termux/boot

# Create startup script
cat > ~/.termux/boot/start-telegram-bot << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Wait for network connectivity
sleep 30

# Navigate to your script directory
cd /data/data/com.termux/files/home/telegram-ai-tagger

# Start the bot
./manage_bot.sh start
EOF

# Make executable
chmod +x ~/.termux/boot/start-telegram-bot

Method 6: Using Termux Services
Create service script:
bash

# Create termux service directory
mkdir -p ~/.termux/services

# Create service file
cat > ~/.termux/services/telegram-bot << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
while true; do
    cd /data/data/com.termux/files/home/telegram-ai-tagger
    python telegram_ai_tagger.py
    sleep 10  # Wait before restarting if crashed
done
EOF

# Make executable
chmod +x ~/.termux/services/telegram-bot

Complete Setup Script for Termux

Create setup_termux.sh:
bash

#!/data/data/com.termux/files/usr/bin/bash

echo "Setting up Telegram AI Bot on Termux..."

# Update packages
pkg update && pkg upgrade -y

# Install required packages
pkg install python git tmux wget -y

# Install Python packages
pip install --upgrade pip
pip install telethon openai

# Create project directory
mkdir -p ~/telegram-ai-tagger
cd ~/telegram-ai-tagger

echo "Downloading script files..."
# Download your script (replace with actual download)
# wget https://your-domain.com/telegram_ai_tagger.py
# wget https://your-domain.com/manage_bot.sh

echo "Making scripts executable..."
chmod +x manage_bot.sh

echo "Setup complete!"
echo "Edit config in telegram_ai_tagger.py first"
echo "Then run: ./manage_bot.sh start"

Monitoring and Maintenance
Check resource usage:
bash

# Check CPU and memory usage
top
htop  # if installed

# Check disk space
df -h

# Check network connections
netstat -tulpn

Log rotation script rotate_logs.sh:
bash

#!/data/data/com.termux/files/usr/bin/bash
LOG_FILE="bot.log"
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt 10485760 ]; then  # 10MB
    mv "$LOG_FILE" "bot_$(date +%Y%m%d_%H%M%S).log"
    gzip "bot_$(date +%Y%m%d_%H%M%S).log"
fi

Add to crontab for automatic log rotation:
bash

# Edit crontab
crontab -e

# Add this line to rotate logs daily at 2 AM
0 2 * * * cd /path/to/your/bot && ./rotate_logs.sh

Troubleshooting Background Running
Check if bot is running:
bash

ps aux | grep -v grep | grep "python telegram_ai_tagger.py"

Check Termux wake lock:
bash

# Prevent device from killing the app
termux-wake-lock

# Release wake lock when not needed
termux-wake-unlock

Check battery optimization:
bash

# Disable battery optimization for Termux
termux-battery-optimization

Monitor with a simple watchdog script watchdog.sh:
bash

#!/data/data/com.termux/files/usr/bin/bash
if ! ps aux | grep -v grep | grep -q "python telegram_ai_tagger.py"; then
    echo "Bot is not running! Restarting..."
    cd /path/to/your/bot
    ./manage_bot.sh start
fi

Recommended Approach

For best results, I recommend:

    Use Method 2 (tmux) for development and testing

    Use Method 4 (management script) for production

    Set up Termux:Boot for auto-start after reboot

    Use the watchdog script with crontab for automatic recovery

This setup will keep your Telegram AI bot running 24/7 in the background on Termux!
