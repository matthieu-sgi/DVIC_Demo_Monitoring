#!/bin/bash

# script is not executed directly, if a command crashes, we have to exit to be notified
set -e 

# Check root access
[[ `id -u` == 0 ]]

# Check minimum python version: >= 3.6
python3 -c "import sys; assert sys.version_info.major == 3; assert sys.version_info.minor >= 6"

# Create folder structure
mkdir -p /opt/dvic-demo-watcher

# Configuration
cat > /opt/dvic-demo-watcher/private.key << EOF
{{ PRIVATE_KEY }}
EOF

cat > /opt/dvic-demo-watcher/config.yml << EOF
uid: {{ NODE_UID }}
private_key_path: /opt/dvic-demo-watcher/private.key
server_root_path: wss://dvic.devinci.fr/demo_watcher/api
latest_update_source: https://dvic.devinci.fr/demo_watcher/release.zip
EOF

cat /opt/dvic-demo-watcher/config.yml

# Service installation
cat > /etc/systemd/system/dvic_demo_watcher.service << EOF
[Unit]
Description=DVIC demo watcher service
After=network.target
Requires=network.target
Type=simple
Restart=always
ExecStart=/opt/dvic-demo-watcher/dvic_client.py
EOF


#TODO install/ upgrade?
# push & run update.py 

systemctl daemon-reload
systemctl enable dvic_demo_watcher
systemctl start dvic_demo_watcher

# No problem, normal exit
exit 0