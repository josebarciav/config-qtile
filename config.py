# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from libqtile import bar, layout, qtile, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
import subprocess
import random
import os

mod = "mod4"
terminal = guess_terminal()

keys = [
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle split/unsplit stack"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
]

# VT switching for Wayland
for vt in range(1, 8):
    keys.append(
        Key(
            ["control", "mod1"],
            f"f{vt}",
            lazy.core.change_vt(vt).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT{vt}",
        )
    )

groups = [Group(i) for i in "123456789"]

layouts = [
    layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=4),
    layout.Max(),
]

widget_defaults = dict(
    font="sans",
    fontsize=12,
    padding=3,
)
extension_defaults = widget_defaults.copy()

def init_widgets_main():
    return [
        widget.GroupBox(),
        widget.Prompt(),
        widget.WindowName(),
        widget.Clock(format='%Y-%m-%d %a %I:%M %p'),
        widget.Systray(),
    ]

def init_widgets_secondary():
    return [
        widget.GroupBox(),
        widget.WindowName(),
        widget.Clock(format='%H:%M'),
    ]

def status_bar(widgets):
    return bar.Bar(widgets, 24, opacity=0.92)

# Run xrandr once at startup to configure outputs
@hook.subscribe.startup_once
def autostart_xrandr():
    log = os.path.expanduser('~/qtile_xrandr.log')
    with open(log, 'a') as f:
        f.write("xrandr startup\n")
        try:
            out = subprocess.check_output(
                ["/usr/bin/xrandr", "--output", "eDP-1",
                 "--primary", "--mode", "1920x1080", "--pos", "0x0", "--rotate", "normal"],
                stderr=subprocess.STDOUT
            )
            f.write(out.decode() + "\n")
        except subprocess.CalledProcessError as e:
            f.write(f"ERROR {e.returncode}: {e.output.decode()}\n")
        try:
            out = subprocess.check_output(
                ["/usr/bin/xrandr", "--output", "HDMI-1-0",
                 "--mode", "3440x1440", "--right-of", "eDP-1", "--rotate", "normal"],
                stderr=subprocess.STDOUT
            )
            f.write(out.decode() + "\n")
        except subprocess.CalledProcessError as e:
            f.write(f"ERROR {e.returncode}: {e.output.decode()}\n")

# Restart Qtile on RandR (screen) changes to avoid duplicate Systray
@hook.subscribe.screen_change
def restart_on_randr(qt, ev):
    qt.cmd_restart()

# screens = [
#     Screen(top=status_bar(init_widgets_secondary())),
# ]

screens = []

# Count connected monitors and append secondary bars
xrandr_cmd = "xrandr | grep -w 'connected' | cut -d ' ' -f 2 | wc -l"
command = subprocess.run(
    xrandr_cmd,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

if command.returncode != 0:
    error = command.stderr.decode("UTF-8")
    logger.error(f"Failed counting monitors using {xrandr_cmd}:\n{error}")
    connected_monitors = 1
else:
    connected_monitors = int(command.stdout.decode("UTF-8").strip())

if connected_monitors > 1:
    for _ in range(connected_monitors - 1):
        screens.append(
            Screen(top=status_bar(init_widgets_main()))
        )

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []

follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),    # gitk
        Match(wm_class="maketag"),       # gitk
        Match(wm_class="ssh-askpass"),   # ssh-askpass
        Match(title="branchdialog"),     # gitk
        Match(title="pinentry"),         # GPG key password entry
    ]
)

auto_fullscreen = True
focus_on_window_activation = "smart"
auto_minimize = True

wl_input_rules = None
wl_xcursor_theme = None
wl_xcursor_size = 24

wmname = "LG3D"
