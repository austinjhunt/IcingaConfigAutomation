"""
Austin Hunt, Sept 16-17, 2019
HostObject module for storing and manipulating Icinga Host object configuration template
"""
from string import Template as tmp


# Class for dynamically building/filling out an Icinga Host object configuration that adapts to different
# arguments passed to it. If argument is not passed (e.g. OS or notes), then it doesn't add the variable to the config.
class HostObject:
    # constructor automatically detects if these columns were provided as arguments and determines the associated values
    def __init__(self, address=None, hostname=None, notes=None, os=None, display_name=None):
        # Let the template be an instance variable with an internally substitutable "body" which will be built using the other
        # instance variables.
        self.template = tmp("object Host \"$hostname\" { $body}")

        # The host name doesn't need to be defined as a 'definition' string, it'll just be substituted into $hostname directly.
        self.hostname = hostname

        # For these variables, give them either their passed value or empty string if that value is none
        self.address_def = "address = \"" + address + "\"" if address is not None else ""
        self.notes_def = "vars.notes = \"" + notes.replace('\n', ' ').replace('\r',
                                                                              '') + "\"" if notes is not None else ""
        self.os_def = "vars.os = \"" + os + "\"" if os is not None else ""
        self.check_command_def = "check_command = \"hostalive\""
        self.display_name_def = "display_name = \"" + display_name + "\"" if display_name is not None else "display_name = \"" + self.hostname + "\""

    def create_object(self):
        config_body = ""
        # Add every instance variable that is neither the 1) template nor 2) the host name to the body of the configuration.
        # Include new lines and tabs.
        for key, value in self.__dict__.items():
            if not isinstance(value, tmp) and key != "hostname":
                config_body += "\n\t" + value
        config_body += "\n"

        # Fill in the template
        obj = self.template.substitute(hostname=self.hostname, body=config_body)
        # Clean the blank lines from the template.
        clean = "\n".join([ll.rstrip() for ll in obj.splitlines() if ll.strip()])  # remove empty lines
        return clean
