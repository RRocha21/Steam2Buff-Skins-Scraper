#!/bin/bash

# Function to run a script and wait for it to finish
run_script_and_wait() {
    echo "Starting script: $1"
    ./Buff2Steam.sh
}

# Function to run a script multiple times concurrently
run_script_concurrently() {
    local num_tasks=$1

    # Array to store the background process IDs
    local pids=()

    # Loop to run the script multiple times concurrently
    for ((i=1; i<=num_tasks; i++)); do
        ./start.sh &
        pids+=($!)  # Store the background process ID
        sleep 10
    done

    monitor_and_maintain_tasks
}

# Function to continuously monitor and maintain the number of tasks
monitor_and_maintain_tasks() {
    while true; do
        # Count the number of running tasks
        num_running_tasks=$(pgrep -c start.sh)
        
        # Calculate the number of tasks to add
        tasks_to_add=$((20 - num_running_tasks))
        
        if [ "$tasks_to_add" -gt 0 ]; then
            echo "Adding $tasks_to_add new tasks..."
            run_script_concurrently "$tasks_to_add"
        fi

        clear  # Clear the terminal to update the display
        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "System Information:"
        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "-----------------------------------------------------------------------------------------------------------------"


        echo "System load: $(uptime | awk -F'[a-z]:' '{print $2}') $(vcgencmd measure_temp | grep -o '[0-9]*\.[0-9]*') C"
        echo "Usage of /: $(df -h / | awk 'NR==2 {print $5}') of $(df -h / | awk 'NR==2 {print $2}')"
        echo "Processes: $(ps aux | wc -l)"
        echo "Memory usage: $(free -m | awk 'NR==2 {print $3/$2 * 100}')%"
        echo "Users logged in: $(who | wc -l)"
        echo "Swap usage: $(free -m | awk 'NR==4 {print $3/$2 * 100}')%"
        echo "IPv4 address for eth0: $(ip addr show eth0 | grep 'inet\b' | awk '{print $2}')"

        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "-----------------------------------------------------------------------------------------------------------------"
        
        # Check the number of running tasks
        num_running_tasks=$(pgrep -c start.sh)
        echo " "
        echo " "
        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "Tasks Information:"
        echo "Number of Running Tasks: $num_running_tasks"
        echo "-----------------------------------------------------------------------------------------------------------------"
        echo "-----------------------------------------------------------------------------------------------------------------"
        
        sleep 60  # Check every 10 seconds
    done
}

# Function to handle cleanup and exit
cleanup_and_exit() {
    echo "Cleaning up and exiting..."
    
    # Kill all background processes
    for pid in "${pids[@]}"; do
        kill -9 "$pid"
    done
    
    exit 0
}

# Trap the keyboard interrupt signal (Ctrl+C) and call cleanup_and_exit function
trap cleanup_and_exit SIGINT

# Example usage

# Start OpenVPN server
sudo systemctl start openvpn-server@server.service
cd ../../../../home/rr/git/

echo "Run the Buff2Steam.sh script..."

cd Buff.Steam-Proxy-Scraper || exit 1
chmod +x Buff2Steam.sh

run_script_and_wait "Buff.Steam-Proxy-Scraper/Buff2Steam.sh"

cd .. || exit 1

echo "Running scripts concurrently..."
cd Buff2Steam-Scraper || exit 1
chmod +x start.sh
run_script_concurrently 20  # Start 100 tasks concurrently in the background

# Start monitoring and maintaining tasks