import arcpy
from datetime import datetime

class ToolValidator:
  # Class to add custom behavior and properties to the tool and tool parameters.

    def __init__(self):
        # set self.params for use in other function
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Customize parameter properties. 
        # This gets called when the tool is opened.
        pr = arcpy.mp.ArcGISProject("CURRENT")
        stedfestingsmetode = self.params[1]
        p4 = self.params[4]
        p5 = self.params[5]
        
        mp = pr.activeMap
        sr = mp.spatialReference
        
        stedfestingsmetode.value = "Vegsystemreferanse - fra | til"
        p4.value = str(datetime.now().date())
        p5.value = sr
        return

    def updateParameters(self):
        # Modify parameter values and properties.
        # This gets called each time a parameter is modified, before 
        # standard validation.
        return

    def updateMessages(self):
        # Customize messages for the parameters.
        # This gets called after standard validation.
        return

    # def isLicensed(self):
    #     # set tool isLicensed.
    # return True

    # def postExecute(self):
    #     # This method takes place after outputs are processed and
    #     # added to the display.
    # return
