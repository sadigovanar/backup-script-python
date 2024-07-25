import os
import subprocess
from datetime import datetime

# Configuration
backup_dir = "/path/to/backup"
sqlfile = "alldatabases.sql"
seafile_tarfile = "Seafile"
seafile_dir = "/opt/seafile"
date = datetime.now().strftime("%Y%m%d")
backup_sqlfile = os.path.join(backup_dir, sqlfile)
backup_seafile = os.path.join(backup_dir, f"{seafile_tarfile}.{date}.tar.bz2")
remote_ip = "server_ip"
remote_user = "user"
remote_backup_dir = "/home/user/bk-server"
mysql_password = 'sql_root_password_here'

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {command}")
        print(result.stderr)
    return result

def check_and_stop_service(service_name):
    """Check if a service is running, and stop it if it is."""
    if subprocess.run(f"pgrep -x {service_name}", shell=True).returncode == 0:
        run_command(f"systemctl stop {service_name}")

def check_and_start_service(service_name):
    """Check if a service is running, and start it if it isn't."""
    if subprocess.run(f"pgrep -x {service_name}", shell=True).returncode != 0:
        run_command(f"systemctl start {service_name}")

# Check and stop services
check_and_stop_service("mysqld")
check_and_stop_service("seafile")
check_and_stop_service("seahub")

# Backup all databases
run_command(f"mysqldump -u root --password='{mysql_password}' --all-databases > {backup_sqlfile}")

# Create a tarball of the Seafile directory
run_command(f"tar cfj {backup_seafile} --exclude={seafile_dir}/ccnet/ccnet.sock --absolute-names {seafile_dir}")

# Secure copy the backup files to the remote server
run_command(f"scp {backup_sqlfile} {backup_seafile} {remote_user}@{remote_ip}:{remote_backup_dir}")

# Delete the local backup files
if os.listdir(backup_dir):
    print("Deleting backup files")
    run_command(f"find {backup_dir} -type f \\( -name '*.sql' -o -name '*.tar.bz2' \\) -delete")

# Start services again
check_and_start_service("mysqld")
check_and_start_service("seafile")
check_and_start_service("seahub")

# Function to restore the database and files
def restore():
    run_command("systemctl stop mariadb")
    run_command("systemctl stop seafile.service")
    run_command("systemctl stop seahub.service")
    run_command("systemctl stop nginx")
    
    run_command(f"mysql -u root --password='{mysql_password}' < {sqlfile}")
    run_command(f"tar xvfj {seafile_tarfile}.tar.bz2 -C /opt/")
    
    run_command("systemctl start mariadb")
    run_command("systemctl start seafile.service")
    run_command("systemctl start seahub.service")
    run_command("systemctl start nginx")

# Call restore function when needed
# restore()
