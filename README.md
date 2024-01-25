# Web3 Reverse Proxy
Unstable PoC implementation of a Web3 reverse proxy.

It was originally developed on **Windows 10 Pro** with **PyCharm 2022.3.1 (Community Edition)** and **Python 3.11**.

## Running on Ubuntu
Tested on two setups
- Raspberry Pi 4 and Ubuntu 20.04.6 LTS ([Ethereum On Raspberry Pi](https://github.com/jimmyisthis/Ethereum-On-Raspberry-Pi) image)
- Raspberry Pi 5 and Ubuntu 23.10

The description below was **tested only on** these two versions of **Ubuntu**, namely **20.04.6 LTS and 23.10**.

## Configuration
A step-by-step process of configuring the environment to run the application on **Ubuntu (20.04.6 LTS or 23.10)**. Depending on the setup, some of the presented steps may (or even should be) skipped.

#### Git setup
There are multiple options for configuring GitHub access to a private repository. One option is as follows (**uses global settings**):
- If necessary, configure your git user
  ```bash
  git config --global user.name 'your username'
  git config --global user.email 'email address'
  ```
- Generate a [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- Set up automatic token authorization
  ```bash
  MY_GIT_TOKEN=xxxxxxxxxxxxxxxx # token generated in the previous step
  git config --global url."https://api:$MY_GIT_TOKEN@github.com/".insteadOf "https://github.com/"
  git config --global url."https://ssh:$MY_GIT_TOKEN@github.com/".insteadOf "ssh://git@github.com/"
  git config --global url."https://git:$MY_GIT_TOKEN@github.com/".insteadOf "git@github.com:"
  ```

#### Repository setup
The repository uses submodules that need additional actions. Once again, one of the possible options of cloning a repository to a local machine:
- Change the directory to the development directory (`~/dev` in this instruction)
  ```bash
  cd ~/dev
  ```
- Clone the repository
  ```bash
  git clone https://github.com/jimmyisthis/web3-reverse-proxy.git
  cd web3-reverse-proxy
  ```
- Initialize submodule
  ```bash
  git submodule init
  git submodule update
  ```

#### Python Configuration
On Ubuntu 23.10, Python 3.11 should already be installed. 

To configure Python 3.11 on Ubuntu 20.04.6 LTS, follow the steps below:
- Make sure that the installed Python version is 3.8.10
  ```bash
  python3 -V
  ```
- Add repository
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt-get update
  ```
- Verify that Python 3.11 is available
  ```bash
  apt list | grep python3.11
  ```
- Install Python 3.11
  ```bash
  sudo apt-get install python3.11
  ```
- Add both Python versions to the update-alternatives
  ```bash
  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2
  ```
- Select Python 3.11 as the default option
  ```bash
  sudo update-alternatives --config python3
  ```
- Ensure that the configuration is correct
  ```bash
  python3 -V
  ```

#### Virtual Environment Prerequisites
In the case of a freshly installed Python 3.11 (or unmodified Ubuntu 23.10 for Raspberry Pi 5 distro), one additional step is required:
- Install one additional package
  ```bash
  sudo apt install python3.11-venv
  ```

## Running the Proxy
Before the first run, you have to create a virtual environment (**venv** in this instruction)

#### Venv Creation
- Change the dir to where the repository is cloned (**~/dev/web3-reverse-proxy** in this instruction)
  ```bash
  cd ~/dev/web3-reverse-proxy
  ```
- Create a virtual environment
  ```bash
  python3 -m venv venv
  ```
- Activate the created virtual environment
  ```bash
  source venv/bin/activate
  ```
- Install required modules (console prompt should start with **(venv)**)
  ```bash  
  python -m pip install -r requirements.txt
  ```
- Deactivate the virtual environment
  ```bash
  deactivate
  ```

You are now ready to run the application.

#### Running the Proxy
With a properly configured virtual environment, running the application still requires a few steps:
- Change the dir to where the repository is cloned (**~/dev/web3-reverse-proxy** in this instruction)
  ```bash
  cd ~/dev/web3-reverse-proxy
  ```
- Activate the created virtual environment
  ```bash
  source venv/bin/activate
  ```
- Edit the configuration file
  ```bash
  nano web3_reverse_proxy/config/conf.py
  ```
  And set `ETH0_BACKEND_ADDR` and `ETH0_BACKEND_NAME` (lines 28 and 29) that correspond to the endpoint(s) you want to connect via the proxy. Double-check the ports. By default, the web3 RPC is available via the port **8545**, so the example configuration may look like 
  this:
  ```python
  ETH0_BACKEND_ADDR = "http://geth-1.local:8545"
  ETH0_BACKEND_NAME = "rpi4 geth-1"
  ```
- Run the proxy
  ```bash
  python web3_reverse_proxy/rproxy.py
  ```
- To terminate the proxy server (and release resources), press `Ctrl-c` and wait for the graceful server shutdown

## Misc Quirks and Tips
As this a work-in-progress project, it may only be stable in its original development environment (**Windows 10 Pro**, **PyCharm 2022.3.1 (Community Edition)** and **Python 3.11**). In its original environment, the proxy was verified to operate correctly for three days. 

#### Examples
There are a few different example cases provided for reference. To run them, follow the original instruction, but call the `rproxy-examples.py` file instead of `rproxy.py`.

Some of the examples require more than a single device (e.g., _example_test_load_balancing_multi_device_setup_), and others require access to the Infura endpoint (which means adding a valid **INFURA API KEY** to the `INFURA_ADDR` variable in the file `conf.py`).

#### Stability issues on Ubuntu
- There may be connection problems right after the first run of the project
  - **Restart to the rescue**
- If the proxy is up and running for an extended period without any incoming RPC calls, it may stop accepting new connections
  - **Restart to the rescue**

#### HTTP Admin Server
By default, the proxy hosts an HTTP server to make monitoring the Proxy status and updating user data easier.

Assuming that the proxy is hosted on a device with an IP `192.168.87.91`, the admin panel can be opened on a web browser via the page (the web browser must be in the same subnet)
```
http://192.168.87.91:6561/HTTP_SERVER_ADMIN_ACCESS_TOKEN`
```

The **HTTP_SERVER_ADMIN_ACCESS_TOKEN** is a token the proxy displays during the launch.

Almost every element in the admin page can be clicked to fetch stats or change settings (e.g., clicking *Proxy Admin Panel* shows the remote console).

## TODO
- Improving the application's stability (i.e., ensuring responsiveness when running).
- Preparing a separate examples directory
  - Include all the examples from the file `rproxy-examples.py`
  - Add more examples during the project development
- Warnings
  - Request parser was implemented for testing purposes only and may fail in a scenario with multiple different RPC queries that were not tested
  - Response parser may fail (only rudimentary parsing)
- Documentation
  - Including architecture
  - User management
  - Billing section
  - Ecosystem (public IP renting)
- Description of multiple setups (including Infura)
- and more...
