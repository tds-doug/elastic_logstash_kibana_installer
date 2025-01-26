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
#   System modules:
#      curl - sudo apt install curl
#
# Usage:
#   python3 elastic_logstash_kibana_installer.py                        # Run the script with a menu
#   python3 elastic_logstash_kibana_installer.py --install-everything   # Full installation with no menu
#
# Disclaimer: This script is provided as-is, and the author assumes no liability
# for any issues arising from its execution. Ensure all system requirements are met
# before running this script.
# ==============================================================================

import json
import logging
import os
import pexpect
import re
import requests
import shutil
import subprocess
import sys
import zipfile
from tkinter import Tk, Button, Label

# ===== VARIABLES =====
DOWNLOAD_DIR = "/tmp/elk_setup"
INSTALL_DIR = "/usr/share"
ELK_DATA_DIR = "/elkdata"

ELASTICSEARCH_VERSION = "8.17.0"
ELASTICSEARCH_USER = "elasticsearch"
ELASTICSEARCH_GROUP = "elasticsearch"
ELASTICSEARCH_PASSWORD = "changemeElasticsearch"
ELASTICSEARCH_PLUGIN_DIR = f"{INSTALL_DIR}/elasticsearch/plugins"
ELASTICSEARCH_SUPER_PW = "changemeSuperUser"
ELASTICSEARCH_GATEWAY_USER = "elastic@invisinet"
ELASTICSEARCH_GATEWAY_PW = "changemeElastic"
ELASTICSEARCH_CATALINA_USER = "catalina@invisinet"
ELASTICSEARCH_CATALINA_PW = "changemeCatalina"	#Recommend changing this value
ELASTICSEARCH_LOGSTASH_USER = "changemeLogstash"
ELASTICSEARCH_LOGSTASH_PW = "logstash"	#Recommend changing this value
ELASTICSEARCH_ROLE_URL = "https://localhost:9200/_security/role"
ELASTICSEARCH_USER_URL = "https://localhost:9200/_security/user"
ELASTICSEARCH_CERT_PATH = "/etc/elasticsearch/certs/http_ca.crt"

LOGSTASH_VERSION = "8.17.0"
LOGSTASH_USER = "logstash"
LOGSTASH_GROUP = "logstash"
LOGSTASH_PASSWORD = "changemeLogstash"	# Recommend changing this value

KIBANA_VERSION = "8.17.0"
KIBANA_USER = "kibana"
KIBANA_GROUP = "kibana"
KIBANA_PASSWORD = "changemeKibana"	# Recommend changing this value
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
    install_output = subprocess.run(["dpkg", "-i", deb_file], check=True)
#    install_output = subprocess.run(["dpkg", "-i", deb_file], check=True, capture_output=True, text=True)

#    if (component == "elasticsearch"):
#        password_match = re.search(r"built-in superuser is : (.*)", install_output.stdout)
#        if password_match:
#            ELASTICSEARCH_SUPER_PW = password_match.group(1).strip()
#        logging.info(f"ELASTICSEARCH_SUPER_PW is {ELASTICSEARCH_SUPER_PW}")
#        logging.info(f"If you lose this reset it via {INSTALL_DIR}/{component}/bin/elasticsearch-reset-password")
    

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

    if (component == "elasticsearch"):
        chown_usergroup = ELASTICSEARCH_USER + ":" + ELASTICSEARCH_GROUP
        elastic_data_dir = ELK_DATA_DIR + "/elastic_data"
        if not os.path.exists(elastic_data_dir):
            os.makedirs(elastic_data_dir)
            subprocess.run(["chmod", "777", elastic_data_dir], check=True)
        subprocess.run(["chmod", "777", elastic_data_dir], check=True)
        subprocess.run(["chown", "-R", chown_usergroup, component_data_logs_dir], check=True) 
    if (component == "kibana"):
        chown_usergroup = KIBANA_USER + ":" + KIBANA_GROUP
        subprocess.run(["chown", "-R", chown_usergroup, component_data_dir], check=True) 
        subprocess.run(["chown", "-R", chown_usergroup, component_data_logs_dir], check=True) 
    if (component == "logstash"):
        chown_usergroup = LOGSTASH_USER + ":" + LOGSTASH_GROUP
        subprocess.run(["chown", "-R", chown_usergroup, component_data_dir], check=True) 
        subprocess.run(["chown", "-R", chown_usergroup, component_data_logs_dir], check=True) 

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
        elasticsearch_keystore_cmd = "/usr/share/elasticsearch/bin/elasticsearch-keystore"
        set_keystore_password = f"echo '{ELASTICSEARCH_SUPER_PW}' | {elasticsearch_keystore_cmd} add bootstrap.password"
        subprocess.run([set_keystore_password], shell=True, check=True, executable='/bin/bash')
        chown_usergroup = ELASTICSEARCH_USER + ":" + ELASTICSEARCH_GROUP
        chown_directory1 = ELK_DATA_DIR + "/elastic_data"
        chown_directory2 = ELK_DATA_DIR + "/logs/elasticsearch"
#        subprocess.run(["chown", "-R", f"{ELASTICSEARCH_USER}:{ELASTICSEARCH_GROUP}", chown_directory], check=True) 
        subprocess.run(["chown", "-R", chown_usergroup, chown_directory1], check=True) 
        subprocess.run(["chown", "-R", chown_usergroup, chown_directory2], check=True) 
      
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
        #create_system_users_and_groups(component)
        enable_systemd_service(component)
        post_install_config(component)

def change_elasticsearch_password(user, new_password):
    """Changes the password for the elasticsearch user"""
    logging.info(f"Changing password for Elasticsearch user {user} ...")

    try:
        # Spawn the password reset command with -i (interactive mode)
        child = pexpect.spawn(f"/usr/share/elasticsearch/bin/elasticsearch-reset-password -i -u {user}")

        # Send confirmation that you want to continue
        child.expect("Please confirm that you would like to continue.*")
        child.sendline("y")

        # Expect the password prompt and send the new password
        child.expect("Enter password for .*:")
        child.sendline(new_password)
        child.expect("Re-enter password for .*:")
        child.sendline(new_password)

        # Wait for the command to complete
        child.expect(pexpect.EOF)
        logging.info(f"Elasticsearch password for user {user} reset successfully!")

    except Exception as e:
        logging.info(f"Error resetting Elasticsearch password for {user}: {e}")

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

def create_system_users_and_groups(component):
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

def post_install_config(component):
    """Configuration that required {component} to be installed"""
    logging.info(f"Configuring {component} post-installation...")
    if (component == "elasticsearch"):
        change_elasticsearch_password("elastic", ELASTICSEARCH_SUPER_PW)
        change_elasticsearch_password(KIBANA_USER, KIBANA_PASSWORD)
        change_elasticsearch_password(LOGSTASH_USER, LOGSTASH_PASSWORD)
        change_elasticsearch_password("kibana_system", "kibana_system")
        change_elasticsearch_password("logstash_system", "logstash_system")
        change_elasticsearch_password("apm_system", "apm_system")
        change_elasticsearch_password("remote_monitoring_user", "remote_monitoring_user")

        define_elasticsearch_roles(component)
        define_elasticsearch_users(component)
    logging.info(f"Post-installation for {component} completed successfully!")

def define_elasticsearch_roles(component):
    """Creating Elasticsearch roles"""
    logging.info(f"Start defining & creating Elasticsearch roles...")
    if (component == "elasticsearch"):
        # Define invisinet_logstash role
        ELASTICSEARCH_ROLE = "invisinet_logstash"
        logging.info(f"Defining & creating {ELASTICSEARCH_ROLE} role...")
        TMP_URL = ELASTICSEARCH_ROLE_URL + "/" + ELASTICSEARCH_ROLE
        ELASTICSEARCH_ROLE_DATA = {
            "cluster": ["manage_logstash_pipelines", "monitor", "monitor_rollup",
                        "monitor_transform", "monitor_snapshot"],
            "indices": [{
                "names": ["invisinet*", "catalina*", "metricbeat*", "auditbeat*",
                          "filebeat*", "heartbeat*", ".monitoring*"],
                "privileges": ["read", "write", "view_index_metadata", "create",
                               "create_index", "create_doc", "manage"],
                "allow_restricted_indices": False
            }],
            "applications": [],
            "run_as": [],
            "transient_metadata": {"enabled": True}
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_ROLE_DATA)

        # Define invisinet_rw role
        ELASTICSEARCH_ROLE = "invisinet_rw"
        logging.info(f"Defining & creating {ELASTICSEARCH_ROLE} role...")
        TMP_URL = ELASTICSEARCH_ROLE_URL + "/" + ELASTICSEARCH_ROLE
        ELASTICSEARCH_ROLE_DATA = {
            "cluster": ["manage_logstash_pipelines", "monitor", "monitor_rollup", 
                        "monitor_transform", "monitor_snapshot"],
            "indices": [{
                "names": ["invisinet*", "metricbeat*", "auditbeat*", "filebeat*", 
                          "heartbeat*", ".monitoring*", ".kibana*"],
                "privileges": ["read", "write", "view_index_metadata"],
                "allow_restricted_indices": False
            }],
            "applications": [{
                "application": "kibana-.kibana",
                "privileges": ["space_all"],
                "resources": ["space:invisinet"]
            }],
            "run_as": [],
            "transient_metadata": {"enabled": True}
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_ROLE_DATA)

        # Define invisinet_ro role
        ELASTICSEARCH_ROLE = "invisinet_ro"
        logging.info(f"Defining & creating {ELASTICSEARCH_ROLE} role...")
        TMP_URL = ELASTICSEARCH_ROLE_URL + "/" + ELASTICSEARCH_ROLE
        ELASTICSEARCH_ROLE_DATA = {
            "cluster": ["monitor"],
            "indices": [{
                "names": ["invisinet*", "metricbeat*", "auditbeat*", "filebeat*", 
                          "heartbeat*", ".monitoring*", ".kibana*"],
                "privileges": ["read", "view_index_metadata"],
                "allow_restricted_indices": False
        }],
        "applications": [{
            "application": "kibana-.kibana",
            "privileges": ["space_read"],
            "resources": ["space:invisinet"]
        }],
        "run_as": [],
        "transient_metadata": {"enabled": True}
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_ROLE_DATA)

        # Define catalina_rw role
        ELASTICSEARCH_ROLE = "catalina_rw"
        logging.info(f"Defining & creating {ELASTICSEARCH_ROLE} role...")
        TMP_URL = ELASTICSEARCH_ROLE_URL + "/" + ELASTICSEARCH_ROLE
        ELASTICSEARCH_ROLE_DATA = {
            "cluster": ["manage_logstash_pipelines", "monitor", "monitor_rollup", 
                        "monitor_transform", "monitor_snapshot"],
            "indices": [{
                "names": ["catalina*", ".kibana*"],
                "privileges": ["read", "write", "view_index_metadata"],
                "allow_restricted_indices": False
        }],
        "applications": [{
            "application": "kibana-.kibana",
            "privileges": ["space_all"],
            "resources": ["space:catalina"]
        }],
        "run_as": [],
        "transient_metadata": {"enabled": True}
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_ROLE_DATA)

        # Define catalina_r0 role
        ELASTICSEARCH_ROLE = "catalina_ro"
        logging.info(f"Defining & creating {ELASTICSEARCH_ROLE} role...")
        TMP_URL = ELASTICSEARCH_ROLE_URL + "/" + ELASTICSEARCH_ROLE
        ELASTICSEARCH_ROLE_DATA = {
            "cluster": ["monitor"],
            "indices": [{
                "names": ["catalina*", ".kibana*"],
                "privileges": ["read", "view_index_metadata"],
                "allow_restricted_indices": False
        }],
        "applications": [{
            "application": "kibana-.kibana",
            "privileges": ["space_read"],
            "resources": ["space:catalina"]
        }],
        "run_as": [],
        "transient_metadata": {"enabled": True}
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_ROLE_DATA)

    logging.info(f"Completed defining & creating {component} roles...")

def define_elasticsearch_users(component):
    """Creating Elasticsearch users"""
    logging.info(f"Start defining & creating Elasticsearch users...")
    if (component == "elasticsearch"):
        # Define invisinet_logstash user
        ELASTICSEARCH_USER = "invisinet_logstash"
        logging.info(f"Defining & creating {ELASTICSEARCH_USER} user...")
        TMP_URL = ELASTICSEARCH_USER_URL + "/" + ELASTICSEARCH_USER
        ELASTICSEARCH_USER_DATA = {
            "password": ELASTICSEARCH_LOGSTASH_PW,
            "roles": [
                "invisinet_logstash", "beats_admin", "ingest_admin",
                "enrich_user", "monitoring_user",
                "remote_monitoring_agent", "remote_monitoring_collector"
            ]
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_USER_DATA)

        # Define Elasticsearch gateway user
        ELASTICSEARCH_USER = ELASTICSEARCH_GATEWAY_USER
        logging.info(f"Defining & creating {ELASTICSEARCH_USER} user...")
        TMP_URL = ELASTICSEARCH_USER_URL + "/" + ELASTICSEARCH_USER
        ELASTICSEARCH_USER_DATA = {
            "password": ELASTICSEARCH_GATEWAY_PW,
            "roles": ["invisinet_rw"]
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_USER_DATA)

        # Define Elasticsearch catalina user
        ELASTICSEARCH_USER = ELASTICSEARCH_CATALINA_USER
        logging.info(f"Defining & creating {ELASTICSEARCH_USER} user...")
        TMP_URL = ELASTICSEARCH_USER_URL + "/" + ELASTICSEARCH_USER
        ELASTICSEARCH_USER_DATA = {
            "password": ELASTICSEARCH_CATALINA_PW,
            "roles": ["catalina_rw"]
        }
        create_elasticsearch_role_user(TMP_URL, ELASTICSEARCH_USER_DATA)

    logging.info(f"Completed defining & creating {component} users...")

def create_elasticsearch_role_user(URL, JSON_DATA):
    response = requests.put(
        URL,
        auth=("elastic", ELASTICSEARCH_SUPER_PW),
        headers={"Content-Type": "application/json"},
        json=JSON_DATA,
        verify=ELASTICSEARCH_CERT_PATH  # SSL certificate verification
    )

    # Log response
    if response.status_code == 200:
        logging.info(f"User successfully created/updated!")
    else:
        logging.info(f"Error: {response.status_code} - {response.text}")

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
    Label(root, text="be installed AFTER Elasticsearch").pack()
    Button(root, text="Install Mapper-size Plugin", command=lambda: install_elasticsearch_plugin("mapper-size")).pack()

    Label(root, text="").pack()
    Label(root, text="The following plugins can only").pack()
    Label(root, text="be installed AFTER Kibana").pack()
    Button(root, text="Install kbnSankeyVis Plugin", command=lambda: install_kibana_plugin("kbnSankeyVis", "https://github.com/uniberg/kbn_sankey_vis/releases/download/v.8.14.1-1/kbnSankeyVis-8.16.0-v2.zip")).pack()

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

