# ==============================================================================
# Script Name: elastic_logstash_kibana_installer.py
# Author: D. Johnson - doug.johnson@invisinet.com
# Description: This script is designed to automate the installation and setup
#              of the Elastic Stack (Elasticsearch, Logstash, Kibana, and modules).
#              If executed with no command line arguments, a menu will be displayed
#              allowing the user to select installation options. Running the script
#              with the command line argument '--install-everything' will bypass
#              the menu and automatically execute all functions for full installation.
#
# Version History:
# ------------------------------------------------------------------------------
# 1.0.0 - Initial release. Basic installation functionality.
#
# Prerequisites:
#   Python modules:
#      tk - sudo apt install python3-tk
#
# Usage:
#   python3 elastic_logstash_kibana_installer.py                        # Run the script with a menu
#   python3 elastic_logstash_kibana_installer.py --install-everything   # Full installation with no menu
#
# Disclaimer: This script is provided as-is, and the author assumes no liability
# for any issues arising from its execution. Ensure all system requirements are met
# before running this script.
# ==============================================================================

import os
import subprocess
import shutil
import logging
import sys
import json
import zipfile
from tkinter import Tk, Button, Label

# ===== CONFIGURATION =====
DOWNLOAD_DIR = "/tmp/elk_setup"
INSTALL_DIR = "/usr/share"
ELK_DATA_DIR = "/elkdata"

ELASTICSEARCH_VERSION = "8.17.0"
ELASTIC_PASSWORD = "changeme"
ELASTICSEARCH_PLUGIN_DIR = f"{INSTALL_DIR}/elasticsearch/plugins"

LOGSTASH_VERSION = "8.17.0"
LOGSTASH_PASSWORD = "changeme"

KIBANA_VERSION = "8.17.0"
KIBANA_PASSWORD = "changeme"
KIBANA_PLUGIN_DIR = f"{INSTALL_DIR}/kibana/plugins"

# ===== LOGGING SETUP =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== HELPER FUNCTIONS =====
def download_and_install(component, version):
    """Downloads and installs a specified component."""
    logging.info(f"Downloading {component} version {version}...")
    #url = f"https://artifacts.elastic.co/downloads/{component}/{component}-{version}-amd64.deb"
    #deb_file = f"{DOWNLOAD_DIR}/{component}-{version}-amd64.deb"
    url = f"https://artifacts.elastic.co/downloads/{component}/{component}-{version}-arm64.deb"
    deb_file = f"{DOWNLOAD_DIR}/{component}-{version}-arm64.deb"

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    subprocess.run(["wget", "-O", deb_file, url], check=True)
    logging.info(f"Installing {component}...")
    subprocess.run(["dpkg", "-i", deb_file], check=True)

    logging.info(f"{component} installed successfully!")

def configure_component(component):
    """Configures a specified component."""
    logging.info(f"Configuring {component}...")
    component_data_dir = ELK_DATA_DIR + "/" + component
    component_data_logs_dir = ELK_DATA_DIR + "/logs/" + component
    if not os.path.exists(ELK_DATA_DIR):
        os.makedirs(ELK_DATA_DIR)
        subprocess.run(["chmod", "777", ELK_DATA_DIR], check=True)
    if not os.path.exists(component_data_dir):
        os.makedirs(component_data_dir)
        subprocess.run(["chmod", "777", component_data_dir], check=True)
    if not os.path.exists(component_data_logs_dir):
        os.makedirs(component_data_logs_dir)
        subprocess.run(["chmod", "777", component_data_logs_dir], check=True)

    subprocess.run(["chmod", "777", "/etc/" + component], check=True)
    yml_file = "/etc/" + component + "/" + component + ".yml"
    if not os.path.exists(yml_file):
        print(f"{component} yml file not found!")
        return
    subprocess.run(["cp", yml_file, yml_file+".orig"], check=True)
    #subprocess.run(["chmod", "666", yml_file], check=True)
    if (component == "elasticsearch"):
        with open(yml_file,'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("path.data:"):
                    lines[i] = f"path.data: /elkdata/elastic_data\n"
                if line.strip().startswith("path.logs:"):
                    lines[i] = f"path.logs: /elkdata/logs/elasticsearch\n"
                if line.strip().startswith("#action.destructive_requires_name:"):
                    lines[i] = f"action.destructive_requires_name: true\n"
                if line.strip().startswith("#cluster.name:"):
                    lines[i] = f"cluster.name: invisinet\n"
    if (component == "kibana"):
        with open(yml_file,'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("#path.data:"):
                    lines[i] = f"path.data: /elkdata/kibana_data\n"
                if line.strip().startswith("      fileName: /var/log"):
                    lines[i] = f"      fileName: /var/log/kibana/kibana.log\n"
                if line.strip().startswith("#server.host:"):
                    lines[i] = f"server.host: 0.0.0.0\n"
                if line.strip().startswith("#server.name:"):
                    lines[i] = f"server.name: \"Invisinet Elastic Host\"\n"
    if (component == "logstash"):
        with open(yml_file,'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("path.data:"):
                    lines[i] = f"path.data: /elkdata/logstash_data\n"
                if line.strip().startswith("path.logs:"):
                    lines[i] = f"path.logs: /elkdata/logs/logstash\n"
                if line.strip().startswith("#api.http.host:"):
                    lines[i] = f"api.http.host: 127.0.0.1\n"
                if line.strip().startswith("#api.http.port:"):
                    lines[i] = f"api.http.host: \"9600\"\n"
    with open(yml_file,'w') as file:
        file.writelines(lines)
    logging.info(f"{component} configured successfully!")

def install(component, version):
    """Installs a selected component from the GUI."""
    if check_installation(component):
        logging.info(f"{component} is already installed.")
    else:
        download_and_install(component, version)
        configure_component(component)
        #create_users_and_groups(component)
        enable_systemd_service(component)

def install_elasticsearch_plugin(plugin_name):
    """Installs the specified plugin."""
    logging.info(f"Installing {plugin_name} plugin for Elasticsearch...")
    if not os.path.exists(ELASTICSEARCH_PLUGIN_DIR):
        os.makedirs(ELASTICSEARCH_PLUGIN_DIR)

    subprocess.run([f"{INSTALL_DIR}/elasticsearch/bin/elasticsearch-plugin", "install", plugin_name], check=True)
    logging.info(f"{plugin_name} plugin installed!")

def install_kibana_plugin(plugin_name, plugin_url):
    """Installs the specified plugin."""
    logging.info(f"Installing {plugin_name} plugin...")
    if not os.path.exists(KIBANA_PLUGIN_DIR):
        os.makedirs(KIBANA_PLUGIN_DIR)

    plugin_file = f"{KIBANA_PLUGIN_DIR}/{plugin_name}.zip"
    subprocess.run(["wget", "-O", plugin_file, plugin_url], check=True)
    with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
        zip_ref.extractall(KIBANA_PLUGIN_DIR)
    if os.path.exists(KIBANA_PLUGIN_DIR + "/kibana"):
        subprocess.run(["mv", KIBANA_PLUGIN_DIR+"/kibana/"+plugin_name, KIBANA_PLUGIN_DIR], check=True)
    logging.info(f"{plugin_name} plugin installed!")

def create_users_and_groups(component):
    """Creating Users and Groups for a specified component."""
    logging.info(f"Creating {component} users and groups...")
    try:
        subprocess.run(["groupadd", component], check=True)
    except:
        print("Group component already exists") 
    try:
        subprocess.run(["useradd", "-r", "-g", component, "-s", "/bin/false", component], check=True)
    except:
        print("User component already exists") 
    logging.info(f"{component} users and groups created successfully!")

def enable_systemd_service(component):
    """Enabling systemd service for a specified component."""
    logging.info(f"Enabling {component} systemd service...")
    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", "elasticsearch"], check=True)
    subprocess.run(["sudo", "systemctl", "start", "elasticsearch"], check=True)
    logging.info(f"Systemd service for {component} enabled successfully!")

def apply_ndjson(file_path):
    """Applies a custom NDJSON file to Elasticsearch."""
    with open(file_path, "r") as f:
        for line in f:
            doc = json.loads(line)
            # Customize this logic to apply each document
            logging.info(f"Applying document: {doc}")

def check_installation(component):
    """Checks if a component is already installed."""
    path = f"{INSTALL_DIR}/{component}"
    return os.path.exists(path)

def clean_up():
    """Deletes downloaded files."""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    logging.info("Clean up complete.")

# ===== GUI MENU =====
def create_menu():
    root = Tk()
    root.title("Invisinet ELK Stack Installer")
    root.geometry(f"{400}x{400}")

    Label(root, text="Select a component to install").pack()

    Button(root, text="Install Elasticsearch", command=lambda: install("elasticsearch", ELASTICSEARCH_VERSION)).pack()
    Button(root, text="Install Logstash", command=lambda: install("logstash", LOGSTASH_VERSION)).pack()
    Button(root, text="Install Kibana", command=lambda: install("kibana", KIBANA_VERSION)).pack()

    Label(root, text="").pack()
    Label(root, text="The following plugins can only").pack()
    Label(root, text="be installed AFTER Kibana").pack()
    Button(root, text="Install kbnSankeyVis Plugin", command=lambda: install_kibana_plugin("kbnSankeyVis", "https://github.com/uniberg/kbn_sankey_vis/releases/download/v.8.14.1-1/kbnSankeyVis-8.16.0-v2.zip")).pack()

    Label(root, text="").pack()
    Label(root, text="The following plugins can only").pack()
    Label(root, text="be installed AFTER Elasticsearch").pack()
    Button(root, text="Install Mapper-size Plugin", command=lambda: install_elasticsearch_plugin("mapper-size")).pack()

    Label(root, text="").pack()
    Button(root, text="Exit", command=lambda: [clean_up(), root.destroy()]).pack()

    root.mainloop()

# ===== MAIN FUNCTION =====
if __name__ == "__main__":
    if "--install-everything" in sys.argv:
        for comp, ver in [("elasticsearch", ELASTICSEARCH_VERSION), ("kibana", KIBANA_VERSION), ("logstash", LOGSTASH_VERSION)]:
            if not check_installation(comp):
                download_and_install(comp, ver)
        install_elasticsearch_plugin("mapper-size")
        install_kibana_plugin("kbnSankeyVis", "https://github.com/uniberg/kbn_sankey_vis/releases/download/v.8.14.1-1/kbnSankeyVis-8.16.0-v2.zip")
        logging.info("All components installed successfully!")
    else:
        create_menu()

