#!/bin/bash

# Prompt the user to choose between Script A and Script B
echo "Which script do you want to start?"
echo "1. Script Steam2Buff"
echo "2. Script Buff2Steam"
read -p "Enter your choice (1 or 2): " choice

# Check the user's choice and execute the corresponding script
case $choice in
    1)
        echo "Starting Script Steam2Buff..."
        # Replace '/path/to/scriptA.sh' with the actual path to Script A
        start-steam.sh
        ;;
    2)
        echo "Starting Script Buff2Steam..."
        # Replace '/path/to/scriptB.sh' with the actual path to Script B
        start-buff.sh
        ;;
    *)
        echo "Invalid choice. Exiting..."
        ;;
esac
