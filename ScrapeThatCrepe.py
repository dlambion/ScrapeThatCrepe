"""
  1) Accesses the first page of results for health inspection information from the Napa County health department website.

  2) Access each inspection of each facility on that page and collect the following information:
     - Facility name
     - Street address
     - City
     - State
     - ZIP code
     - Inspection date
     - Inspection type
     - Inspection grade
     - Item number and description for each out-of-compliance violation

  3) Print out JSON file of information

  4) Print the collected information to the console in an easy-to-understand format.

"""


#Author: Danielle Lambion

import json
import requests
from bs4 import BeautifulSoup
import usaddress



#Page url for Napa County Inspection Reports
page_url = (
    "http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=03/01/2017&kw1=&kw2=&kw3="
    "&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar"
)

"""
Main method
"""
def main():
    inspectionUrls = getInspectionPages()
    inspectionInfo = getInspectionInfo(inspectionUrls)
    printToConsole(inspectionInfo)
    writetoJSON(inspectionInfo)

"""
Access the first page of results for health inspection information from the Napa County health department website.
Finds the links to every inspection report for the first page of the website.

return: links - array of links to the individual inspection reports.
"""
def getInspectionPages():
    site = "http://ca.healthinspections.us"
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'lxml')
    links = []
    for link in soup.find_all('a'):
        if (link.get('href')[0] == '.'):
            urlOriginal = link.get('href')
            url = urlOriginal.replace(".","",2)
            links.append(site + url)
    return links

"""
Access each inspection of each facility on that page and collect information.
Information is parsed by tags and formatted to strings.

param: links - An array of url links for each inspection report.
return: businesses - A 2d array containing containing the information collected for each business.
"""
def getInspectionInfo(links):
    businesses = []
    for link in links:
        topSection = []
        gradingSection = []
        grade = []
        inspectionInfo = []
        page = requests.get(link);
        soup = BeautifulSoup(page.content, 'lxml')
        violations = parseMainTable(soup)
        for div in soup.find_all('div'):
            if(div.get('class') == ['topSection']):
                for span in div.find_all('span'):
                    topSection.append(span.get_text().strip())
            elif(div.get('class') == ['page2Content']):
                for table in div.find_all('table'):
                    if(table.get('class') == ['totPtsTbl']):
                        gradingSection.append(table.get_text().strip())
                        grade.append((gradingSection[len(gradingSection)-1])[-1:])

        inspectionInfo = parseTopSection(topSection) + grade
        inspectionInfo.append(violations)
        businesses.append(inspectionInfo)
    return businesses

"""
Parses information gathered from the top section of the site's html for only
the information needed.

param: topSectionArr - An array of strings containing all information gathered from the top section.
return: topSection - An array of strings containing only need information from the top section.
"""
def parseTopSection(topSectionArr):
    topSection = []
    topSection.append(topSectionArr[0])
    topSection.append(topSectionArr[2])
    address = parseAddress(topSectionArr[4])
    for str in address:
        topSection.append(str)
    topSection.append(topSectionArr[9])
    return topSection

"""
Parses business' full address into street address, city, state, and zipcode.

param: address - A string that is the business' full address.
return: parsedAddress - An array containing the strings of the street address, city, state, and zipcode.
"""
def parseAddress(address):
    addressTuples = usaddress.parse(address)
    city = ""
    streetAddress = ""
    for tup in addressTuples:
        if 'StreetName' in tup[1] or tup[1] == 'AddressNumber':
            if streetAddress:
                streetAddress += " " + tup[0]
            else:
                streetAddress = tup[0]
        elif tup[1] == 'PlaceName':
            if city:
                city += " " + tup[0]
            else:
                city = tup[0]
        elif tup[1] == 'StateName':
            state = tup[0]
        elif tup[1] == 'ZipCode':
            zipcode = tup[0]
    parsedAddress = [streetAddress, city.replace(',',''), state, zipcode]
    return parsedAddress

"""
Parses main table of the site's html containing all compliance tests and retrieves out
of compliance violations.

param: soup - Beautiful soup object from the inspection's site.
return: violations - A string of all the out of compliance violations for each business.
"""
def parseMainTable(soup):
    complianceTests = []
    for table in soup.find_all('table'):
        if table.get('class') == ['insideTable']:
            for tr in table.find_all('tr'):
                if tr.get_text().strip()[:1].isdigit() and tr.get_text().strip()[-1:].isdigit():
                    complianceTests.append(tr.get_text().strip())
    violations = formatViolations(complianceTests)
    return violations

"""
Formats the strings of the compliance violations by removing tags and unnecessary text.

return: violations - the string of compliance violations for each business formatted.
"""
def formatViolations(complianceTests):
    violations = ""
    for test in complianceTests:
        str = test[:-7].strip()
        if violations:
            violations += ', ' + str
        else:
            violations += str
    return violations

"""
Iterates gathered inspection information to be printed to console.

param: inspectionInfo - A 2d array containing of the information gathered on each business.
"""
def printToConsole(inspectionInfo):
    neededInfo = ['Facility Name: ', 'Inspection Date: ', 'Street Address: ', "City: ", 'State: ', 'Zipcode: ',
                  'Inspection Type: ', 'Inspection Grade: ', 'Out of Compliance Violations: ']
    for i in range(len(inspectionInfo)):
        for j in range(len(inspectionInfo[i])):
            print(neededInfo[j] + inspectionInfo[i][j])
        print('\n')

"""
Creates a nested dictionary keyed by business name.
The dictionary for each business is keyed by information type.
Writes file called results.json to disk drive after being formatted into a dictionary.

param: InspectionInfo -- A 2d array of the information gathered on each business.
"""
def writetoJSON(inspectionInfo):
    neededInfo = ['Facility Name: ', 'Inspection Date: ', 'Street Address: ', "City: ", 'State: ', 'Zipcode: ',
                  'Inspection Type: ', 'Inspection Grade: ', 'Out of Compliance Violations: ']
    businessDict = {}
    for i in range(len(inspectionInfo)):
        businessInfoDict = {}
        for j in range(len(inspectionInfo[i])):
            businessInfoDict.update({neededInfo[j]: inspectionInfo[i][j]})
        businessDict.update({inspectionInfo[i][0]: businessInfoDict})
    with open('results.json', 'w') as outFile:
        json.dump(businessDict, outFile)

if __name__ == '__main__':
    main()
