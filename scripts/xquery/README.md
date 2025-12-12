# XQuery scripts

These xquery files were used to investigate XML content.

They were tested with saxon; can be installed according to this gist:

https://gist.github.com/joewiz/f44a29c61ae23b16b478dfabe0fefbac

With an alias of `saxonxq` as described in that gist, use the following
syntax to specify the xquery file and the input xml document:

```shell
saxonxq scripts/xquery/continuing-footnotes.xq  -s:data/MEGA_A2_B005-00_ETX.xml
```
