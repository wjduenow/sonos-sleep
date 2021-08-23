Requires Python3.3+

###Building and Saving Local Docker Image for import into QNAP from m1 Max into Intel
docker build --platform=linux/amd64 -t sonos-sleep . && docker save sonos-sleep > sonos-sleep.tar
