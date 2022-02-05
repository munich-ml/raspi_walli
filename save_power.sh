#!/bin/bash     save_power.sh
#               https://learn.pi-supply.com/make/how-to-save-power-on-your-raspberry-pi/#turn-off-hdmi-output

# Switch off USB and Ethernet
echo '1-1' |sudo tee /sys/bus/usb/drivers/usb/unbind

# Switch off HDMI
sudo /opt/vc/bin/tvservice -o