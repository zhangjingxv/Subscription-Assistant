#!/usr/bin/env python3
# RSS Reader - Unix Philosophy: Do one thing well
import sys
from urllib.request import urlopen
from xml.etree.ElementTree import fromstring

for item in fromstring(urlopen(sys.argv[1]).read()).findall('.//item')[:10]:
    print(f"• {item.findtext('title')}\n  {item.findtext('link')}\n")