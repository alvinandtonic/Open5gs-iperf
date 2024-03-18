# Open5Gs ft. UERANSIM

This is a [POWDER](https://powderwireless.net/) profile that automatically instantiates a full simulated 5g core network and UE RAN. It uses [Open5GS](https://github.com/open5gs/open5gs) for the 5c core, spread across n physical nodes, and uses [UERANSIM](https://github.com/aligungr/UERANSIM) v3.1.1 to simulate a gNB and UE devices.

This profile creates and registers a changeable number of UEs. There is a script at `/local/repository/scripts/connect-all-ues.sh` that can be run on sim-ran node to start and create PDU sessions (and therefore interfaces) for all 10 UEs at once, as well as test them all for internet connectivity.

<br />The webui server of open5gs can be accesed on the node running Open5Gs. For more information visit [Open5gs:webUI](https://www.sharetechnote.com/html/OpenRAN/OR_open5gs_webui.html)
<br /><br />Use following command to access webui on remote server
<br />
ssh -L 9090:localhost:9999 {powder user-name}@pc{machine number}.emulab.net
