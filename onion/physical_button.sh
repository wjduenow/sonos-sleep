#!/bin/ash

#Check to see if curl is installed, if not then install
if ! curl -V COMMAND &> /dev/null
then
    echo "COMMAND could not be found, installing curl"
    opkg install curl
    exit
fi

# set the input pin
IN_PIN=19
WEBHOOK=http://wjduenow.myqnapcloud.com/sleep?room=Brynn&secret_key=mixelplk
LOCK_FILE=/tmp/yolo.lock

# set the state direction of the pin
fast-gpio set-input $IN_PIN

while true
do

	# get the state value '0' or '1' from the pin
	# - '0': means the button is pressed
	# - '1': means the button is relased
	# NOTE: make sure the 'GPI19' string matches the $PIN number
	state=$(fast-gpio read $IN_PIN | awk '/Read GPI19:/ {print $4}')

	# if the pin state is '0', this means the button is being pressed
	if [ "$state" = "0" ]; then
		echo "YOLO Button Engaged..."

		if [ -f "$LOCK_FILE" ]; then
			# check if the button is already in lock mode (the button is pressed and locked)
	        	# in this case, we just show the followingg message and skip.
			echo "Command Loaded & Locked!"
			echo ">Release Button to Cancel."
        	else

            		# when the button is pressed and not in lock mode, 
            		# we go ahead and ping the $WEBHOOK url AND create a lock file.
			curl -X POST -d {} $WEBHOOK
			touch $LOCK_FILE
			echo "Engaging Command..."
		fi

	else
       	 	# if the pin state is '1', this means the button is being released
        	# we delete the lock file to clear the state
		[ -f $LOCK_FILE ] && rm $LOCK_FILE
		echo "YOLO Button ready!"
	fi

	sleep 1
	clear
done
