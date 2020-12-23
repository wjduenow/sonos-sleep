Requires Python3.3+

###Building and Saving Local Docker Image for import into QNAP
docker build -t sonos-sleep . && docker save sonos-sleep > sonos-sleep.tar
