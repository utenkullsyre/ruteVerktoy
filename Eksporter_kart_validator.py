import arcpy

class ToolValidator:
  # Class to add custom behavior and properties to the tool and tool parameters.

    def __init__(self):
        # set self.params for use in other function
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Customize parameter properties. 
        # This gets called when the tool is opened.
        pr = arcpy.mp.ArcGISProject("CURRENT")
        layOuts = pr.listLayouts()
        self.params[0].value = [x.name for x in layOuts] 
        #self.params[0].filter.list = [x.name for x in layOuts] 
        return

    def updateParameters(self):
        pr = arcpy.mp.ArcGISProject("CURRENT")
        layOuts = [x.name for x in pr.listLayouts()]
        formater = ["EPS","SVG","PDF","JPG","PNG"]
        # Modify parameter values and properties.        
        # This gets called each time a parameter is modified, before         
        # standard validation.
        verdiTabell0 = list(self.params[0].value.exportToString().split(";"))
        verdiTabell1 = list(self.params[1].value.exportToString().split(";"))
        
        self.params[0].value = list(dict.fromkeys(verdiTabell0))
        self.params[1].value = list(dict.fromkeys(verdiTabell1))
        
        return

    def updateMessages(self):
        # Customize messages for the parameters.
        # This gets called after standard validation 
        
        return

    # def isLicensed(self):
    #     # set tool isLicensed.
    # return True

    # def postExecute(self):
    #     # This method takes place after outputs are processed and
    #     # added to the display.
    # return
