A python-based i3blocket that displays a timer.

## Dependencies

* i3blocks 1.5+
* python3 3.9+

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
# The placeholder substrings `{start_time}` and `{timer}` will be replaced before executing
# the command.
# 
# Keep in mind that the PATH that i3blocks uses may be different 
# from the one in your terminal. I use: 
# `/usr/bin/notify-send -c alarm -- "Timer is up!" "{timer} ({start_time}) timer is up!"`
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

# Labels, labels are free text, in order to get out of the box support
# dependency to fonts was removed, but you may want to install a font that
# supports icon glyphs like fontawesome or nerdfonts and labels with symbols
# like:
#  * \uf04b (play icon)
#  * \uf04c (pause icon)
#  * \uf251 (hourglass-start icon)
#
# (default: running:)
running_label=foo
# (default: paused:)
paused_label=bar
# (default: timer:)
stopped_label=baz
```

## How to use

|    action     |               |
| ------------- | ------------- |
|  left click   | Start / pause / resume. |
|  scroll up    | Increment timer by `increment`. |
|  scroll down  | Decrement timer by `increment`. |
|  middle click | If defined, `read_input_command` is executed and its `stdout` is parsed.<br><br>The expected format is either `timer=<new timer name>` or `[-+]<time>` where `<time>`'s format can be an integer, a string of the form 3h, 3h20m, 2700s, 1h30m30s or a string of the form 3:00:00, 3:20:00, 45:00, 1:30:30. <br><br>If just `<time>` is passed, the `start_time` is set to `time`;if `+<time>` is passed, `time` is added to the current `start_time`; if `-<time>` is passed, `time` is reduced from `start_time` (capped at 0). |
| right click | Resets the timer back to the last defined `start_time` (i.e. cancels the current timer). |
