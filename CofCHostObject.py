import constants
from HostObject import HostObject
import re
"""
Austin Hunt, Sept 18, 2019
Module for adapting the generic bulk object creator to CofC's network
Subclass of CofCHost object, but add a method that dives deeper into variable definitions by
parsing hostname
OZ-App/Service-Detail

"""


class CofCHostObject(HostObject):
    def __init__(self, address=None, hostname=None, notes=None, os=None, display_name=None):
        #super().__init__(self)  # keep the inheritance of superclass
        super(CofCHostObject,self).__init__(address,hostname,notes,os,display_name)
        # New variables custom to CofC
        self.networkzone_def = None
        self.year_def = None
        self.service_def = None
        self.detail_def = None
        self.temp_def = "vars.temporary = [\"disable ssh\", \"disable notifications\"]"
        self.role_mappings = {
            'DB': 'Database',
            'SBX': 'Sandbox',
            'APP': 'Application',
            # 'ICX':'Java Web Container', # Correct?
            'MQ': 'RabbitMQ',
            'WFL': 'Workflow',
            # 'ERP': 'Enterprise Resource Planning',
            'ESM': 'Ellucian Solution Manager',
            'SQL': 'MySQL',
            'MW': 'Middleware',
            'WEB': 'Web Server',
            'SA': 'Icinga Satellite',
            'M0': 'Master'
        }
        self.os_mappings = {
            'R': 'Red Hat',
            'W': 'Windows',
            'U': 'Ubuntu',
            'C': 'CentOS',
            'V': 'Virtual Appliance',
            'F': 'Fedora',
            'P': 'PAN-OS',
            'L': 'Linux',


        }
        self.zone_mappings = {
            'M': 'Management',
            'P': 'Production',
            'T': 'Test',
            'D': 'Development'
        }
        # Can only use host name to set variables if hostname matches the naming scheme (YYOZ-A/S-DDDDD); define instance variable for pattern
        self.name_scheme_pattern = r'^(([0-9]{2})?(([A-Z]{2})|([a-z]{2})))\-[0-9A-Za-z]+\-[a-zA-Z0-9]+(\.(guest\.vm\.)?cougars\.int)?$'
        # Pattern to match beginning YYOZ pattern vs just beginning OZ pattern
        self.year_oz_pattern = r'^[0-9]{2}(([A-Z]{2})|([a-z]{2}))\-.*'
        # Pattern to match just beginning OZ pattern
        # regex pattern matching any XX-yyyyyy... naßme
        self.oz_pattern = r'^(([A-Z]{2})|([a-z]{2}))\-.*'
        self.set_vars()

    # return boolean representing whether or not host name matches the cofc naming scheme
    def matches_name_scheme(self):
        return True if re.match(self.name_scheme_pattern, self.hostname) else False

    # method that sets hostname-based vars if naming scheme is matched
    def set_vars(self):
        if self.matches_name_scheme():
            if self.os_def == None:      
                # Check if superclass set this already     
                self.set_os()  # calls the set_year method internally if included
            self.set_networkzone()
            self.set_service()
            self.set_detail()

    # Setter methods
    # method to set the os_def variable

    def set_os(self):
    
        # First check the year_oz_pattern other wise oz_pattern will match inaccurately if year_oz_pattern is present
        if re.search(self.year_oz_pattern, self.hostname):  # can proceed with defining os
            self.os_def = "vars.os = \"" + \
                self.get_os(True) + "\"" if self.get_os(True) is not None else ""
            # Set the year_def
            self.set_year()
        elif re.search(self.oz_pattern, self.hostname):
            self.os_def = "vars.os = \"" + \
                self.get_os(False) + "\"" if self.get_os(False) is not None else ""
       

    # Method to set the year_def variable
    def set_year(self):
        self.year_def = "vars.purchase_year = \"" + self.get_year() + "\""

    # Method to set the networkzone_def variable
    def set_networkzone(self):
        self.networkzone_def = "vars.network_zone = \"" + self.get_networkzone() + "\""

    # Method to set the service_def variable
    def set_service(self):
        self.service_def = "vars.service = \"" + self.get_service() + "\""

    def set_detail(self):
        detailstr = self.get_detail()
        self.detail_def = "vars.detail = \"" + detailstr + "\"" if detailstr != "" else None

    # Helper getter methods
    # helper method that takes the hostname and outputs the os based on the first letter
    def get_os(self, includes_year):
        try:
            os_char = self.hostname[2] if includes_year else self.hostname[0]
            res = self.os_mappings[os_char.upper()]
        except Exception as e:
            print(e)
            print("For host:",self.hostname)
        return res

    # Outputs the year based on first two characters of hostname
    def get_year(self):
        return "20" + self.hostname[:2]

    # Outputs the network zone based on last character of first section of host name
    def get_networkzone(self):
        # last character of first section before - character
        zone_char = self.hostname.split("-")[0][-1]
        return self.zone_mappings[zone_char.upper()]

    # Outputs the service based on middle section of hostname
    def get_service(self):
        return self.hostname.split("-")[1]

    def get_detail(self):
        # this one's fun. lots of different strings can be found here.
        # first, address names ending with a number, indicating an indexer; assume a max string of 3 digits for indexing.
        # use regex to get that number
        indexer = self.get_indexer()
        # check for specific strings indicating role
        role = self.get_role()
        rolestr = "role = " + role + "; " if role is not None else ""
        return (indexer + rolestr)
    def get_indexer(self): 
        #print("Getting index...")
        end_num_pattern = r'([0-9]{1,3})((\.guest\.vm)?\.cougars\.int)?$'
        m1 = re.search(end_num_pattern, self.hostname)
        indexer = ""
        if m1:
            #print("Matched an index")
            # trim out terminating domain
            end_num_pattern = r'([0-9]{1,3})$'
            num = re.search(end_num_pattern,m1.group()).group()
            # to be included as part of the detail
            indexer = "indexer = " + str(num) + "; "
        else: 
            #print("No indexer...")
            pass
        return indexer

    def get_role(self):
        # from last section of hostname, get the string until numbers start
        role = ""
        for c in self.hostname.split("-")[-1]:
            if c.isdigit():
                break
            role += c
        try:
            return self.role_mappings[role.upper()]
        except:
            return None
