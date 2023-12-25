#!/usr/bin/python3

import argparse
import random
import re
import time
from bs4 import BeautifulSoup
from termcolor import colored as clr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

"""This tool is used to gather js files, by going to the list of endpoints given to the tool."""

### PARSER
p = argparse.ArgumentParser()
p.add_argument(
        '-l',
        '--list',
        dest="eps",
        required=True,
        help="Target endpoints. Can hold both .js and regular endpoints."
        )
p.add_argument(
        '-o',
        '--output',
        dest="output",
        default="jspider-res.txt",
        help="Output file of the scan."
        )
p.add_argument(
        '-v',
        '--verbose',
        dest="verb",
        action="store_true",
        help="Print error messages, if they occur."
        )
p.add_argument(
        '-t',
        '--target',
        dest="targets",
        required=True,
        help="Give targets separated by comma i.e: twitter,twimg"
        )
args = p.parse_args()

### USER AGENTS
user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246", "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/99.0.1150.36", "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko", "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0", "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.6; rv:105.0) Gecko/20100101 Firefox/105.0", "Mozilla/5.0 (X11; Linux i686; rv:105.0) Gecko/20100101 Firefox/105.0", "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0", "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.34", "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.34", "Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko"]

### FUNCTIONS
def uagen():
    # Generate a random user-agent for the requests
    return user_agents[random.randint(0,len(user_agents)-1)]

def full_request(ep):
    # Use headless browser to get all js files from a site
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    agent = uagen()
    chrome_options.add_argument(f"user-agent={agent}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)
    for _ in range(3):
        try:
            # Gotta figure out a way to get /business/hub contents
            driver.get(ep)  # Opening the page and getting it's source
            time.sleep(13)
            page_content = driver.page_source

            unique_js = [] # Getting a bunch of JS files from by executing some JS.
            #const uniqueJsFiles = [...new Set(htmlContent.match(/["\']https?:\/\/([^"\']*\.(mjs|js))["\']/g))];
            #const uniqueJSFiles = [...new Set(htmlContent.match(/["'](https?:)?\/\/([^"']*\.(mjs|js)(\?[^"']*)?)["']/g))];
            unique_js_unclean = driver.execute_script('''
                const htmlContent = document.documentElement.outerHTML;
                const regex = /["'](https?:)?\/\/([^"']*\\.(mjs|js)(\\?[^"']*\\?)?)["']/g;
                const uniqueJSFiles = [...new Set(htmlContent.match(regex))];
                return uniqueJSFiles;
            ''')
            for js in unique_js_unclean:
                unique_js.append(js.strip('"'))

            driver.quit()   # Close browser
        except TimeoutException:
            if args.verb != False:
                print("[",clr("ERR","red"),"]",ep,"Connection error!")
        else:
            return page_content, unique_js

def extract_js(text, valid_sites):
    # Get js files from text
    js = []
    soup = BeautifulSoup(text, 'lxml')
    for tag in soup.find_all("script", src=True):
        for v in valid_sites:
            if v in tag["src"]:
                if re.search("/[0-9]+[-_\.]",tag["src"]) == None:
                    if tag["src"] not in js:
                        js.append(tag["src"])
    for tag in soup.find_all("link", href=True):
        for v in valid_sites:
            if v in tag["href"]:
                if re.search("/[0-9]+[-_\.]",tag["href"]) == None:
                    if ".js" in tag["href"] or ".mjs" in tag["href"]:
                        if tag["href"] not in js:
                            js.append(tag["href"])
    return js

def get_file(file):
    # Get a file
    ls = []
    with open(file,"r") as f:
        for e in f:
            ls.append(e.rstrip())
    return ls

### SCRIPT
if __name__ == "__main__":
    # List of endpoints
    eps = get_file(args.eps)

    # Making sure our targets are put into a list
    try:
        valid = args.targets.split(",")
    except Exception:
        valid = args.targets

    # List of JS files
    files = []

    # Get JS files on each endpoint within eps
    # and place them into the monitor object
    count = 0
    for e in eps:
        count += 1
        print("[",clr(f"{count}/{len(eps)}","green"),"]",e)
        try:
            rsp, jsfiles = full_request(e)
        except Exception:
            rsp = None
            jsfiles = None
        if rsp != None:
            extractedjs = extract_js(rsp, valid)
        else:
            continue
        if extractedjs != None:
            for js in extractedjs:
                if js not in files:
                    files.append(js)
        if jsfiles != None:
            for js in jsfiles:
                if js not in files:
                    files.append(js)

    with open(args.output,"w") as jsfile:
        for js in files:
            jsfile.write(f"{js}\n")
