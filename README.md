# Squint - Blink Security Camera Scheduler

## Background
The Blink Security Cameras are pretty awesome, unfortunately, the scheduling for turning monitoring on and off is lousy, its done at the Sync Module (Their Hub) level, so a schedule applies to every Camera associated with it - In a nutshell, its not possible to schedule individual cameras. 

**What is the impact of this?** Say you have 6 cameras around your property, but only want the front door monitored during the day, well tough you can't, Its all or nothing! Actually, there is one method, you have to buy an additional Sync Module just for that camera.

This is not an oversight of Blink,  hundreds of customers have made the same request over the past couple of years (Take a look at the blink community forums). As yet, all Blink have said is "They would like to add it".  

After buying 6 Blink Cameras and 2 Sync Modules, I didn't have much appetite for spending more, but we needed the ability to add specific schedules for some of the cameras, as well as download the videos for long-term storage - So I wrote Squint!

Please keep in mind this a few hours of keyboard-bashing and this is the first release, so if you have any problem, please either
* Open an Issue with details (and I'll try to fix it)
* Just delete it 

## Introduction
Squint is a script that allows the automation and control of individual Blink Cameras, with:
 
- [x] Multiple schedules for each camera for enabling/disabling Motion Detection
- [x] Automatically builds its own configuration file, based upon you Blink Cameras
- [ ] Scheduled downloading of new videos to your server/NAS/Laptop (WIP)
- [ ] Scheduled taking of new photo snaps

# Warning
Blink do not publish their API details, they do no officially allow 3rd party access. But as long as they are not abused, they seem to unofficially tolerate it. 

When doing the initial configuration make use of Squints "simulate" features. When live testing, leave 60 seconds between tests. Then when going live, minimise the number of times you run it, my recommendation is at most, once an hour. 

**You have been warned - Blink can and will disable accounts of customers who hammer their servers. If this happens you will need to contact them to get it reactivated.**

## Installation
When I get time, I'll add an autosetup.py, but the simplest installation is as follows:

1. Create a python3.5+ virtualenv (My environment is python 3.7)
2. Clone the repository, or download the zip file
3. Install the required libraries, with the virtualenv activated, run the following:

```
pip install -r requirements.txt
```
## Usage 

### Initial Configuration
Squint automatically generates your initial configuration for you, it retrieves a list of your cameras from Blink, which it uses to build a boilerplate configuration file, this will include your credentials and a basic schedule for each camera. 

To do this, run Squint with the following parameters:
```
squint.py config generate "<YOUR_BLINK_ID>" "<YOUR_BLINK_PASSWORD>"
```
This will generate < install path >/etc/squint.yml file, which is in YAML format, you can edit this with any text editor and tweak times and motion detection status etc. 

**Notes:**
* Squint expects to find the etc/squint.yml in the same directory as it self
* The time format for **from_time** and **until_time fields**, is 24hr, i.e. 1200 and 1200 (NOTE no colon)
* The motion detection value must be "true" or "false" all lower case
* Being a YAML file, white spacing is critical 
* Credentials are stored in plain text. Do not deploy this script onto a shared system. 
* Running this command again, will force the existing file to be overwritten. Which is useful if you make a mistake, but be aware, you will lose any modifications you have made.

### Testing / Simulating 
In order to avoid the need to constantly connect to the Blink servers, Squint has a feature that allows you to save a copy of the data that Blink sends. You can then use this to test your configuration without fear of sending too many requests to Blink, this can also be used for regenerating the configuration file.

To pull the data from Blink and save it locally, you should first generate your initial config (as shown above), then run:
```
squint.py debug save 
```
This will generate the "blink_results.obj" which can now be used for testing. 
To use the saved data, just run a command as you normally would. just pass one of the following switches
 ```
-t
--testresponse
```
So for example, to regenerate the configuration file from the saved data, run the following
```
squint.py config generate "<YOUR_BLINK_ID>" "<YOUR_BLINK_PASSWORD>" --testresponse
```
To test your configuration against the saved data, run the following
```
squint.py push execute --testresponse
```
Please see below for more details on the "push execute"

### Scheduling (Motion Detection)
First of all, Squint does not arm/disarm your Sync Modules, only Motion Detection on each camera. For Squint to do its job. you will need to update your
Sync Module schedule(s) in the Blink mobile app, so it remains armed 24/7, or at least at the times you schedule Squint tp enable Motion Detection.

Once happy with the configuration, Squint can connect to the Blink servers, and attemmpt to apply the desired setting
```
squint.py push execute
```
In order to automate this on an ongoing basis, simple add this to your crontab or scheduler. Please do head the warning
section above.




## TODO
- [ ] Add "Days" to schedule
- [ ] Allow data to be saved when generating initial config (removes need for "debug save")
- [ ] Replace use of click.echo() with proper logging
- [ ] Add exception handling
- [ ] Split classes and namespace
- [ ] Add autosetup.py script
- [ ] Add an overview of the configuration file
- [ ] Add unit testing
- [ ] Implement clip downloading
- [ ] Implement photo snaps
- [ ] Add simulate against live (So changes are only indicated)



 
## Thanks
This scripts is 100% reliant upon work done by 

* Blinkpy - https://github.com/fronzbot/blinkpy
* Click - https://click.palletsprojects.com/

