import os
import argparse
import subprocess

def is_installed(package):
    output = subprocess.run(["dpkg", "-s", package], capture_output=True, text=True)
    return "Status: install ok installed" in output.stdout

def install_zabbix(skip_installed):
    # Update package list
    os.system('sudo apt update')
    
    # Install Zabbix repository if not installed or skip not requested
    if not skip_installed or not is_installed('zabbix-release'):
        os.system('wget https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4%2Bubuntu22.04_all.deb')
        os.system('sudo dpkg -i zabbix-release_6.0-4+ubuntu22.04_all.deb')
        os.system('sudo apt update')

    # Install Zabbix server, frontend, agent, nginx if not installed or skip not requested
    zabbix_packages = ['zabbix-server-mysql', 'zabbix-frontend-php', 'zabbix-nginx-conf', 'zabbix-sql-scripts', 'zabbix-agent', 'nginx']
    if not skip_installed or not all(is_installed(pkg) for pkg in zabbix_packages):
        os.system('sudo apt install ' + ' '.join(zabbix_packages))

def setup_database(db_host, db_port, db_name, db_user, db_password, skip_installed):
    # Install MySQL server if not installed or skip not requested
    if not skip_installed or not is_installed('mysql-server'):  
        os.system('sudo apt install mysql-server')

    # Create initial database
    os.system(f'sudo mysql -h{db_host} -P{db_port} -u{db_user} -p{db_password} -e "create database {db_name} character set utf8mb4 collate utf8mb4_bin"')
    os.system(f'sudo mysql -h{db_host} -P{db_port} -u{db_user} -p{db_password} -e "grant all privileges on {db_name}.* to \'{db_user}\'@\'%\'"')

    # Import initial schema and data
    os.system(f'sudo zcat /usr/share/doc/zabbix-sql-scripts/mysql/server.sql.gz | mysql -h{db_host} -P{db_port} -u{db_user} -p{db_password} {db_name}')  

def configure_zabbix(db_host, db_port, db_name, db_user, db_password, zabbix_domain):
    # Update DBPassword in zabbix_server.conf
    zabbix_config_file = '/etc/zabbix/zabbix_server.conf'
    if os.path.exists(zabbix_config_file):
        with open(zabbix_config_file, 'r') as file:
            data = file.readlines()
    else:
        print(f"Warning: Zabbix config file {zabbix_config_file} not found. Skipping configuration.")
        return
    data = [f'DBPassword={db_password}\n' if 'DBPassword=' in line else line for line in data]
    data = [f'DBUser={db_user}\n' if 'DBUser=' in line else line for line in data]
    data = [f'DBPort={db_port}\n' if 'DBPort=' in line else line for line in data]
    data = [f'DBHost={db_host}\n' if 'DBHost=' in line else line for line in data]
    data = [f'DBName={db_name}\n' if 'DBName=' in line else line for line in data]
    with open('/etc/zabbix/zabbix_server.conf', 'w') as file:  
        file.writelines(data)

    # Configure Nginx
    with open('/etc/nginx/conf.d/zabbix.conf', 'w') as f:
        f.write(f'''server {{
    listen 80;
    server_name {zabbix_domain};
    root /usr/share/zabbix;
    index index.php;

    location / {{
        try_files $uri $uri/ =404;
    }}

    location ~ \.php$ {{
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }}
}}''')

    # Start Zabbix server, agent and nginx processes
    os.system('sudo systemctl restart zabbix-server zabbix-agent nginx php7.4-fpm')
    os.system('sudo systemctl enable zabbix-server zabbix-agent nginx php7.4-fpm')

def uninstall_zabbix():  
    # Stop Zabbix and Nginx processes
    os.system('sudo systemctl stop zabbix-server zabbix-agent nginx php7.4-fpm')
    os.system('sudo systemctl disable zabbix-server zabbix-agent nginx php7.4-fpm')
    
    # Uninstall Zabbix packages  
    os.system('sudo apt purge zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent -y')
    os.system('sudo apt autoremove -y')

    print("Zabbix uninstalled successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Zabbix')
    parser.add_argument('--db-host', help='Hostname or IP address of the database server')
    parser.add_argument('--db-name', help='Name of the Zabbix database')
    parser.add_argument('--db-port', default=3306, help='Port number of the database server')  
    parser.add_argument('--db-user', help='Username for connecting to the database')
    parser.add_argument('--db-password', help='Password for connecting to the database. User should have root privileges.')
    parser.add_argument('--zabbix-domain', help='Domain name for the Zabbix web interface')  
    parser.add_argument('--skip-installed', action='store_true', help='Skip installation of packages that are already installed')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall Zabbix and remove all related packages')
    args = parser.parse_args()

    if args.uninstall:
        uninstall_zabbix()
    else:
        if not all([args.db_host, args.db_name, args.db_user, args.db_password]):
            parser.error("--db-host, --db-name, --db-user and --db-password are required for installation.")
        
        install_zabbix(args.skip_installed)
        setup_database(args.db_host, args.db_port, args.db_name, args.db_user, args.db_password, args.skip_installed)
        if not args.zabbix_domain:
            parser.error("--zabbix-domain is required for installation.")

        configure_zabbix(args.db_host, args.db_port, args.db_name, args.db_user, args.db_password, args.zabbix_domain)
        print("Zabbix deployed successfully")
