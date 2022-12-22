#-------------------------------------------------------------------------------
# Name:       Eksporter kart til EPS, JPG, PDF og SVG
# Purpose:
#
# Author:      tobors
#
# Created:     08.02.2021
# Copyright:   (c) tobors 2021
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
import os

layout = arcpy.GetParameter(0)
eksport_format = arcpy.GetParameter(1)
eksport_folder = arcpy.GetParameterAsText(2)

def eksporterKart(layout,eksport_format, eksport_folder):
    
    valgteLayouter = [x.value for x in layout]

    #Velger det aktive prosjektet
    prj = arcpy.mp.ArcGISProject("CURRENT")
    arcpy.AddMessage("Her er lista over formater: {}".format(' - '.join(eksport_format)))
    arcpy.AddMessage("Her er mappa: {}".format(eksport_folder))
    arcpy.AddMessage("Disse layoutene skal eksporteres: {}".format(valgteLayouter))    
    
    layouter = [x for x in prj.listLayouts() if x.name in [x.value for x in layout]]
    
    
    #Henter ut den aktive layouten
    for ly in layouter:
        #Henter ut navn på layout som skal brukes senere
        kartNavn = "Kartet mett" 
        try:
            kartNavn = ly.name
        except Exception as e:
            arcpy.AddMessage("Finner ikke layout navn, bruker defaultnavn\n{}".format(e))
        finally:
            pass
        arcpy.AddMessage("\n------------- Eksporterer layout: {}-------------".format(kartNavn))
        for format in eksport_format:
            if format == 'EPS':
                arcpy.AddMessage("--- eksporterer til {}".format(format))
                ly.exportToEPS(r"{}\{}".format(eksport_folder, kartNavn)) 
            elif format == 'SVG':
                arcpy.AddMessage("--- eksporterer til {}".format(format))
                ly.exportToSVG(r"{}\{}".format(eksport_folder, kartNavn))
            elif format == 'PDF':
                arcpy.AddMessage("--- eksporterer til {}".format(format))
                ly.exportToPDF(r"{}\{}".format(eksport_folder, kartNavn))
            elif format == 'JPG':
                arcpy.AddMessage("--- eksporterer til {}".format(format))
                ly.exportToJPEG(r"{}\{}".format(eksport_folder, kartNavn), resolution=300)
            elif format == 'PNG':
                arcpy.AddMessage("--- eksporterer til {}".format(format))
                ly.exportToPNG(r"{}\{}".format(eksport_folder, kartNavn), resolution=300)

#Eksporterer ut layout til EPS, SVG, PDF og JPEG. eksport_folder er fil-banen til mappa som kartene skal lagres i


#skriv inn "eksporterKart(*mappe du skal eksportere kart til*)" i python-vinduet og kjør kommandoen

eksporterKart(layout, eksport_format, eksport_folder)