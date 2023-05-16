#!/bin/bash

# script is not executed directly, if a command crashes, we have to exit to be notified
set -e 

# Check root access
[[ `id -u` == 0 ]]

# Check minimum python version: >= 3.6
python3 -c "import sys; assert sys.version_info.major == 3; assert sys.version_info.minor >= 6"

# Create folder structure
mkdir -p /opt/dvic-demo-watcher
cd /opt/dvic-demo-watcher

# Configuration
cat > /opt/dvic-demo-watcher/private.key << EOF
{{ PRIVATE_KEY }}
EOF

cat > /opt/dvic-demo-watcher/config.json << EOF
{
    "uid": "{{ UID }},
    "private_key_path": "/opt/dvic-demo-watcher/private.key",
    "server_root_path": "{{ SERVER_ROOT_PATH }}",
    "preauth_source": {{ PREAUTH_SOURCE }}
    "latest_install_source": "{{ UPDATE_SOURCE }}",
    
}
EOF

cat /opt/dvic-demo-watcher/config.json

# Service installation
cat > /etc/systemd/system/dvic_demo_watcher.service << EOF
[Unit]
Description=DVIC demo watcher service
After=network.target
Requires=network.target
Type=simple
Restart=always
ExecStart=/opt/dvic-demo-watcher/main.py
EOF


# Update can be done with SSHSCript later
# Only the initial install is required here
# The initial package download is very simple
# {{ DOWNLOAD_KEY }} is a one time use key to download the package
# The update script is the scritp in updater.py 

cat > /opt/dvic-demo-watcher/updater.py << EOF
{{ UPDATER_SCRIPT }}
EOF


# with set -e is the script fails the installation is marked as unsuccessful
python3 /opt/dvic-demo-watcher/updater.py {{ DOWNLOAD_KEY }}

systemctl daemon-reload
systemctl enable dvic_demo_watcher
systemctl start dvic_demo_watcher

# No problem, normal exit
exit 0