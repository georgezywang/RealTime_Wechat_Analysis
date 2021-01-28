# Wechat_Analysis

## Obtaining the Key to *.db
open WeChat, without logging in. Type `lldb -p $(pgrep WeChat)` in terminal. You should see some output, with the last two lines similar to
```
Executable module set to "/Applications/WeChat.app/Contents/MacOS/WeChat".
Architecture set to: x86_64h-apple-macosx-.
```
You should also be prompted to the `lldb` interface. Issue the command `br set -n sqlite3_key`. You should see something like `Breakpoint 1: 2 locations.`, ignore any errors. Type c in the terminal for continue. Log in WeChat and then type `memory read --size 1 --format x --count 32 $rsi`. You should see output of the form 
```
0x000000000000: 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
0x000000000000: 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
0x000000000000: 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
0x000000000000: 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
```
Save it to the a txt file and run `utils/KeyParser.py` to obtain a key. That key will allow you to open db files stored in WeChat.

## References
```
https://www.macworld.co.uk/how-to/how-turn-off-mac-os-x-system-integrity-protection-rootless-3638975/
https://blog.csdn.net/u013051748/article/details/108394306
https://www.jianshu.com/p/90224ab9cdf2
```