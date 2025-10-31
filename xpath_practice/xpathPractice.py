from lxml import html
from htmlLibrary import *

# Notes
# xpath(argument)
#
# INPUT: argument //a : '//' -> searches anywhere in the tree
#                'a'  -> tag name to look for <a> elements
# OUTPUT: Returns a lxml.html.HtmlElement object - a live element from the tree

htmlTree = html.fromstring(html_code)

# 1. Grab all link elements
links = htmlTree.xpath('//a') 
print("Links:", links) # returns <a> elements?

# 2. Grab all link urls
linkUrl = htmlTree.xpath('//a/@href')
print("Hrefs:", linkUrl)

# 3. All titles
titles = htmlTree.xpath('//h2/text()')
print("Titles:", titles)

# 4. Only the one that contains 'Python'
python_titles = htmlTree.xpath('//h2[contains(., "Python")]/text()')
print("Python Titles:", python_titles)

# 4a. Title that contains "Master C++"
cpp_titles = htmlTree.xpath('//h2[contains(., "Mastering C++")]/text()')
print("CPP Titles:", cpp_titles)
# 5. All prices