#!/bin/bash

# if [ $(id -u) -ne 0 ]
#   then echo "Please run as root"
#   exit
# fi

# # Create a directory for the installation
# mkdir -p /opt/dvic_demo_watcher/

# # Fetch the file from github
# curl -O https://raw.githubusercontent.com/matthieu-sgi/DVIC_Demo_Monitoring/main/node/client/dvic_client.py

# # Move the file to the installation directory
# mv dvic_client.py /opt/dvic_demo_watcher/

# # Create a service file
# cat <<EOF > /etc/systemd/system/dvic_demo_watcher.service

# Log into a file 

echo "Starting the installation of the DVIC Demo Watcher" >> /home/wanikatako/dvic_demo_watcher.log