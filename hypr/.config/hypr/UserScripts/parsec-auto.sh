#!/bin/bash
# Lắng nghe sự kiện chuyển đổi cửa sổ
socat -U - UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock | while read -r line; do
    if [[ ${line:0:14} == "activewindow>>" ]]; then
        if [[ "$line" == *"parsecd"* ]]; then
            hyprctl dispatch submap passthru
        else
            hyprctl dispatch submap reset
        fi
    fi
done