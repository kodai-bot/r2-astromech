#!/bin/bash
echo "🤖 Starting R2 Astromech Development Environment"
echo "Running on: central-ai"
echo "Python: /home/seu/r2_astromech/r2_venv/bin/python"
echo "Working dir: /home/seu/r2_astromech"

# Activate virtual environment
source r2_venv/bin/activate

# Start tmux session with labeled windows
tmux new-session -d -s r2_dev -n 'main'
tmux new-window -n 'logs' -t r2_dev
tmux new-window -n 'testing' -t r2_dev
tmux send-keys -t r2_dev:logs 'tail -f logs/*.log' Enter
tmux attach-session -t r2_dev
