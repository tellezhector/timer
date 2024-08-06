A python-based i3blocket that displays a timer.

## Dependencies

* i3blocks 1.5

* A font that can render the following 3 utf-8 chars:
  * \uf04b (play icon)
  * \uf04c (pause icon)
  * \uf251 (hourglass-start icon)
  
  [fontawesome.com](https://fontawesome.com)'s free version has all three.

## Blocket configuration

### Minimal blocket configuartion

```ini
[timer]
command=~/path/to/executable
format=json
interval=1
```

### Optional configuration:

```ini
# How many seconds to increase / decrease the timer on mouse scroll
# (default: 60)
increments=60

# How many seconds to start the blocket at
# (default: 300)
start_time=300

# A command to execute when the timer runs out.
#
# The placeholder substring `{start_time}` will be replaced before executing
# the command.
# 
# Keep in mind that the PATH that i3blocks uses may be different 
# from the one in your terminal. I use: 
# `/usr/bin/notify-send -c alarm -- "Timer is up!" "{start_time} timer is up!"`
# (deafult: None)
alarm_command=/usr/bin/foo --bar biz

# Any command that produces stdout from user input. I use
# `/usr/bin/rofi -dmenu` for convenience but you can use something as simple
# as printing the content of a file.
# (default: None)
read_input_command=/usr/bin/foo --bar biz

# Options for `colorize` are:
# - never
# - colorful
# - colorful_on_negatives
# - red_on_negatives
# (default: never)
colorize=red_on_negatives

# Options for `time_format` are:
# - pretty
# - clock
#
# pretty:  5m, 10m30s, 3s,    8h4m3s
# clock: 5:00, 10:30,  00:03, 8:04:03
# (default: pretty)
time_format=pretty

# A font to apply to the blocket.
# (default: None)
font=Roboto

# A path to write logs to. Useful for debugging.
# (default: None)
log_file=/tmp/timer_log.txt
```

## How to use

* Left click to start / pause a timer.

* Scroll up to increment timer.

* Scroll down to decrement timer.

* Middle click to execute `read_input_command`, the `stdout` from the command
  will be parsed as the new `start_time`.

  If you are using `time_format=pretty`, the input is expected in either 
  integers or strings in "pretty format" (300, 5m, 2h30m).

  If you are using `timer_format=clock` the input is expected in either integers 
  or string in "clock format" (300, 5:00, 2:30:00).

* Right click resets the timer back to the last defined `start_time` (i.e. 
  cancels the current timer).
