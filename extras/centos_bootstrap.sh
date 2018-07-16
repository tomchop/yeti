### You'll need to run this as a user with escalated privileges.

### Create the MongoDB Yum repository

cat << EOF > /etc/yum.repos.d/mongodb-org-4.0.repo
[mongodb-org-4.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.0.asc
EOF

### Prepare the field for Yarn
curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -
wget https://dl.yarnpkg.com/rpm/yarn.repo -O /etc/yum.repos.d/yarn.repo

### Update the OS
yum update -y && yum upgrade -y

### Install the YETI Dependencies
yum groupinstall "Development Tools" -y
yum install epel-release
yum install python-pip git mongodb-org python-devel libxml2-devel libxslt-devel zlib-devel redis firewalld yarn -y
pip install --upgrade pip

### Install YETI
git clone https://github.com/yeti-platform/yeti.git
cd yeti
pip install -r requirements.txt
yarn install

### Secure your instance
# Add firewall rules for YETI
systemctl enable firewalld
systemctl start firewalld
firewall-cmd  --permanent --zone=public --add-port 5000/tcp
firewall-cmd --reload

# Prepare for startup
systemctl enable mongod
systemctl start mongod

# Launch Yeti
cd yeti
./yeti.py webserver
