import arcpy
import os
import requests
import regex as r

def ScriptTool(innDatasett, fraAttributt, tilAttributt, koordinatSystem, query):
    # Script execution code goes here
    
    #Setter opp env parametre
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mp = aprx.activeMap
    arcpy.env.addOutputsToMap = True
    arcpy.env.overwriteOutput = True
    
    
    # arcpy.AddMessage("{0} - {1} - {2} - {3}".format(innDatasett, fraAttributt, tilAttributt, koordinatSystem))
    
    #
    fc = innDatasett
    fcNavn = arcpy.Describe(fc).name
    
    #Lager nytt datasett, laster over data fra input-data og legger til nydatasett i kartet
    nyDatasett = arcpy.management.CreateFeatureclass(arcpy.env.workspace, fcNavn + "_rute", "POLYLINE", fc,"DISABLED","DISABLED",koordinatSystem)
    arcpy.Append_management(fc, nyDatasett)
    arcpy.management.AddField(nyDatasett, "kommentar", 'TEXT')
    mp.addDataFromPath(nyDatasett)
    
    #Legger relevante felt i liste som skal brukes i UpdateCursor
    fields = ["OID@","SHAPE@", fraAttributt,tilAttributt, "Kommentar"]
    
    #Kommentar variabel som skal legges inn i 
    kommentar = ""

    #debugdata
    polylinje = ""
    koordinatsystem = arcpy.Describe(nyDatasett)
    testdata = ""

    def hentVegsysrefKorrd(vegsystemReferanse):
        
        urlKoord = "https://nvdbapiles-v3.atlas.vegvesen.no/veg?vegsystemreferanse=" + str(vegsystemReferanse)
        # print(urlKoord)
        
        r = requests.get(urlKoord)
        
        # print(r.text)
        
        if r.status_code == 200:
            # print('Success!')
            resultat =  r.json()
               
            testdata = resultat
            
            pktWKT = resultat['geometri']['wkt']
            koordinat = pktWKT[pktWKT.find("(")+1:pktWKT.find(")")].split(" ")[0:2]
            
            return [koordinat]

            
            
            
        elif r.status_code != 200:
            print('Not Found.')
            kommentar = "Kunne ikke hente vegsystemreferanse-koordinat"
            
            return ["Error", r.text]
        
        


        
        

    def hentRute(fraKoord, tilKoord):
        urlRute = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v2_0/open/routingservice?"
        # print("inne i hentRute", fraKoord, tilKoord)
        
        PARAMS = {
            'stops':";".join([",".join(fraKoord),",".join(tilKoord)]),
            'returnDirections':"false",
            'returnGeometry':'true',
            'format':'json'
        }
        
        # print(PARAMS['stops'])
        
        r = requests.get(url = urlRute, params = PARAMS)
        
        #debug kode
        # print(r.text)
        
        results = r.json()
        ruteGeometri = results['routes']['features'][0]['geometry']['paths']
        # print(len(ruteGeometri))
        
        
        features = []

        for feature in ruteGeometri:
            # Create a Polyline object based on the array of points
            # Append to the list of Polyline objects
            linje = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for coords in feature]),koordinatsystem.spatialReference)
            # print("Spatialreference", linje.spatialReference.exportToString())
            polylinje = linje

                
            features.append(
                linje
                )
        
        return  features

    delstrekninger = ""

    #Velger bare objekt nr 19
    with arcpy.da.UpdateCursor(nyDatasett, fields, query) as updateCursor:
    # with arcpy.da.UpdateCursor(nyDatasett, fields) as updateCursor:  
        

        for index,row in enumerate(updateCursor):
            kommentar = "" 
            print(row)
            radPrint = "{0} {1} {2} - {3}".format(row[0], row[4], row[2], row[3])
            # arcpy.AddMessage(radPrint)
            # print(u'{0}, {1}, {2}, {3}'.format(row[0], row[1], row[2], row[3]))
            arcpy.AddMessage("\n\n-----------------------------------------------\nForsøker å laste ned geometri for ID: {}  -- Pkt fra: {} | Pkt til: {}\n".format(row[0], row[2], row[3]))
            
            # if index == 6: # There's gotta be a better way.
            #     break
            if index != 19: # There's gotta be a better way.
                    pass
            
            if row[2] is None or row[3] is None:
                print("Her e det ingenting!")
                kommentar = "FEIL: Mangler enten fra eller til referanse"
                
                rad = [row[0],None,row[2], row[3], kommentar]
                testdata = [rad]
                
                arcpy.AddWarning("Fant ikke fra eller til referanse, går til neste rad\n\n")
                updateCursor.updateRow(rad)
                
                continue
            
            pktFra = hentVegsysrefKorrd(row[2])
            # print("Punkt fra {}".format(pktFra))
            
            pktTil = hentVegsysrefKorrd(row[3])
            # print("Punkt til {}".format(pktTil))
            # arcpy.AddMessage("\n\nID: {}  -- Pkt fra: {} | Pkt til: {}\n\n".format(row[0], pktFra, pktTil)) 
            
            
            if pktTil[0] == "Error" or pktFra[0] == "Error":
                manglerKoordinat = []
                responseData = []
                if pktFra[0] == "Error":
                    manglerKoordinat.append("Punkt fra")
                    responseData.append("Pkt fra responsedata: \n{}".format(pktFra[1]))
                if pktTil[0] == "Error":
                    manglerKoordinat.append("Pkt til")
                    responseData.append("Pkt til responsedata: \n{}".format(pktTil[1]))
                kommentar = "FEIL: Fant ikke koordinat på: {}".format(",".join(manglerKoordinat))
                
                rad = [row[0],None,row[2], row[3], kommentar]
                testdata = [rad]
                arcpy.AddWarning("Objekt med ID {}: {}\n{}\n\n".format(row[0], kommentar,",".join(responseData)))
                updateCursor.updateRow(rad)
                
            
                continue
            
            if pktTil[0] != "Error" or pktFra[0] != "Error":
                rute = hentRute(pktTil[0], pktFra[0])
                testdata = rute
                # print(rute)
                # rute = hentRute(pktTil, pktFra, row[0])
                # Insert new rows that include the county name and the x and y coordinate
                # pair that represents the county center

                for r in rute:
                    # print("Her er jeg ", r)
                    # print("Kommentar før linjegeometri\n" + kommentar + "{}".format(len(kommentar)))
                    kommentar = "Linje-geometri hentet ned"
                    rad = [row[0],r,row[2], row[3], kommentar]
                    testdata = [rad]
                    arcpy.AddMessage("Lastet ned linje geometri for objekt med id {}\n".format(row[0]) + radPrint + "\n\n" )
                    updateCursor.updateRow(rad)

            
            
            
            # A list that will hold each of the Polyline objects
    return

# This is used to execute code if the file was run but not imported
if __name__ == '__main__':

    # Tool parameter accessed with GetParameter or GetParameterAsText
    innDatasett = arcpy.GetParameterAsText(0)
    fraAttributt = arcpy.GetParameterAsText(1)
    tilAttributt = arcpy.GetParameterAsText(2)
    koordinatSystem = arcpy.GetParameterAsText(3)
    query = arcpy.GetParameterAsText(4)
    
    ScriptTool(innDatasett, fraAttributt, tilAttributt, koordinatSystem, query)
    
    # Update derived parameter values using arcpy.SetParameter() or arcpy.SetParameterAsText()