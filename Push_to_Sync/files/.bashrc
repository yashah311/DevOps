# .bashrc

[ -z "$PS1" ] && return

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# User specific aliases and functions
. $HOME/.alias


