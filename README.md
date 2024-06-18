# Stack Overflow Enterprise Webhook Report
A Python script for Stack Overflow Enterprise that creates a CSV report of configured webhooks. You can see an [example](https://github.com/jklick-so/soe_webhooks/blob/main/Examples/webhooks.csv) of what the output looks like in the Examples directory.

All data obtained via this script is handled locally on the device from which the script is run. The script does not transmit data to other parties, such as Stack Overflow. This script is entirely read only, with no ability to change/add content on your Stack Overflow instance.

This script is offered with no formal support from Stack Overflow. If you run into issues using the script, please please open a GitHub issue and/or reach out to the person who provided it to you. You are also welcome to edit the script to suit your needs.

## Requirements
* Stack Overflow Enterprise and a user account with admin permissions
* Python 3.x ([download](https://www.python.org/downloads/))
* Operating system: Linux, MacOS, or Windows
* Chrome browser

## Setup
[Download](https://github.com/jklick-so/soe_webhooks/archive/refs/heads/main.zip) and unpack the contents of this repository

To install the required open source libraries for Python:
* Open a terminal window (or, for Windows, a command prompt)
* Navigate to the directory where you unpacked the files
* Install the dependencies: `pip3 install -r requirements.txt`

## Usage
In a terminal window, navigate to the directory where you unpacked the script. 
Run the script using the following format, replacing the URL your own:

`python3 soe_webhooks.py --url "https://SUBDOMAIN.stackenterprise.co"`

At the beginning of the script, a small Chrome window will appear, prompting you to login to your instance of Stack Overflow Enterpise. After logging in, the Chrome window will disappear and the script will proceed in the terminal window.

The script typically takes less than a minute to run. As it runs, it will continue to update the terminal window with the status. When the script completes, it will indicate the the CSV has been exported, along with the name of file. You can see an [example](https://github.com/jklick-so/soe_webhooks/blob/main/Examples/webhooks.csv) of what the output looks like in the Examples directory.
