#!/usr/bin/env python3
import urllib.request, sys
from bs4 import BeautifulSoup, Tag

URL = "https://ddosecrets.com/index.php?title=Special:Categories&offset=&limit=500"
HTTP_TIMEOUT=10 # Seconds

# GET categories page
req = urllib.request.Request(URL, data=None)
response = None
newurl = None
response = urllib.request.urlopen(req, timeout=HTTP_TIMEOUT)

# Parse the first <ul> looking for <li> entries
html = response.read()
parsed_html = BeautifulSoup(html, features="html.parser")
categories = parsed_html.find("ul")
if( categories == None ):
	sys.stderr.write("Unable to find categories. Dying...\n")
	sys.exit(1)
with open("categories.csv", "w") as f:
	for item in categories.findAll("li"):
		if isinstance(item, Tag):
			(category, count) = item.text.split("(")
			category = category.rstrip()
			category = category.encode("ascii", "ignore").decode("ascii") # Strip weird <200f><200e> garbage
			count = int(count.split(" ")[0])
			f.write("%s,%d\n" % (category,count))
