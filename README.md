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

# An optional name for your timer.
# (default: timer)
timer_name=timer

# Format string for your blocket's text.
#
# Placeholders are:
# 
# elapsed_time   (float, measured in seconds)
# remaining_time (float, measured in seconds)
# start_time     (integer, measured in seconds)
# timer_name     (string)
#
# In addition to all regular f-string formats, there are two 
# formatters for numeric values:
#
# - pretty:  5m, 10m30s,     3s,  8h4m3s
# - clock: 5:00,  10:30,  00:03, 8:04:03
#
# Examples:
# If you have a 5m timer named 'code review' and 30s have passed
# {remaining_time:pretty}                     → 4m30s
# {remaining_time:clock}                      → 4:30
# {elapsed_time:clock}                        → 00:30
# {elapsed_time:pretty}                       → 30s
# {elapsed_time:.2f}                          → 30.00
# {timer_name} {remaining_time:pretty}        → code review 4m30s
# {timer_name:.6} {remaining_time:pretty}     → code r 4m30s
# {remaining_time:pretty}/{start_time:pretty} → 4m30s/5m
#
# (default: {remaining_time:pretty})
text_format={remaining_time:pretty}/{start_time:pretty}

# A command to execute when the timer runs out.
#
# The command takes the same treatement as `text_format` so 
# you can use placeholders
# 
# Keep in mind that the PATH that i3blocks uses may be different 
# from the one in your terminal. I use: 
# `/usr/bin/notify-send -c alarm -- "Timer is up!" "{timer_name} ({start_time:pretty}) timer is up!"`
# (deafult: None)
alarm_command=/usr/bin/foo --bar biz

# Any command that produces stdout from user input. I use
# `/usr/bin/rofi -dmenu` for convenience but you can use something as simple
# as printing the content of a file.
#
# This command also takes the same treatment as `text_format` and
# `alarm_command` in regards of substituting placeholders.
#
# (default: None)
read_input_command=/usr/bin/foo --bar biz

# Options for `colorize` are:
# - never
# - colorful
# - colorful_on_negatives
# - red_on_negatives
#
# (default: never)
colorize=red_on_negatives

# A path to write logs to. Useful for debugging.
# (default: None)
log_file=/tmp/timer_log.txt

# Labels are free text, but you may want to install a font that
# supports icon glyphs like fontawesome or nerdfonts and labels 
# with symbols like:
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

# This is inherited from i3blocks
# see: https://github.com/vivien/i3blocks#i3bar-properties
# which is in turn referenced from:
# https://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail
# options are 'none' or 'pango'.
# (default: none)
markup=pango
```

## How to use

|    action     |               |
| ------------- | ------------- |
|  left click   | Start / pause / resume. |
|  scroll up    | Increment timer by `increment`. |
|  scroll down  | Decrement timer by `increment`. |
|  middle click | If defined, `read_input_command` is executed and its `stdout` is parsed.<br><br>The expected format is either `property=<new value>` or `[-+]<time>` where `<time>`'s format can be an integer, a string of the form 3h, 3h20m, 2700s, 1h30m30s or a string of the form 3:00:00, 3:20:00, 45:00, 1:30:30. <br><br>If just `<time>` is passed, the `start_time` is set to `time`;if `+<time>` is passed, `time` is added to the current `start_time`; if `-<time>` is passed, `time` is reduced from `start_time` (capped at 0).<br><br> For `property=<new value>`, the properties that can be overwritten are `timer_name`, `text_format`, `alarm_command`, `read_input_command`, `running_label`, `stopped_label`, `paused_label`, `color_option`.|
| right click | Resets the timer back to the last defined `start_time` (i.e. cancels the current timer). |
