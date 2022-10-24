set -euox pipefail

flag=false

while getopts 's' opt; do
    case $opt in
        s) flag=true ;;
        *) echo 'Error in command line parsing' >&2
            exit 1 ;;
    esac
done
echo "$flag"
if ! "$flag"; then 
    if [ -f /etc/os-release ]; then
        # freedesktop.org and systemd
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        # linuxbase.org
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        # For some versions of Debian/Ubuntu without lsb_release command
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        # Older Debian/Ubuntu/etc.
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/SuSe-release ]; then
        # Older SuSE/etc.
        ...
    elif [ -f /etc/redhat-release ]; then
        # Older Red Hat, CentOS, etc.
        ...
    else
        # Fall back to uname, e.g. "Linux <version>", also works for BSD, etc.
        OS=$(uname -s)
        VER=$(uname -r)
    fi


    echo "INSTALLING DEPENDENCIES"
    echo "-----------------------"

    if [[ $OS == *"Ubuntu"* ]]; then 

        sudo dpkg --purge docker docker-engine docker.io containerd runc
        sudo apt-get update
        sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

        sudo mkdir -p /etc/apt/keyrings

        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg

        echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        sudo apt-get install -y python3 python3-pip
        

    elif [[ $OS == *"CentOS"* ]]; then 	
        sudo yum remove docker \
                        docker-client \
                        docker-client-latest \
                        docker-common \
                        docker-latest \
                        docker-latest-logrotate \
                        docker-logrotate \
                        docker-engine
        sudo yum install -y yum-utils
        sudo yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        sudo yum -y install python3 python3-pip

    else
        echo "Distro not supported, please manually install ansible and docker, then run 'ansible-playbook setup.yml'"
    fi 

    export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

    pip3 install --user ansible #openstacksdk

    echo "ENSURE MTU FOR DOCKER BRIDGE MATCHES HOST"
    echo "-----------------------"
    sudo systemctl restart docker

    MTU=$(ip -4 r show default | awk '$5 {print $5}' | xargs ip a show dev | grep mtu | awk '$3 {print $5}')

    sudo touch /etc/docker/daemon.json

sudo tee "/etc/docker/daemon.json" > /dev/null <<EOF
{
    "mtu":$MTU
}
EOF

    sudo systemctl restart docker
fi 

ansible-playbook setup.yml
