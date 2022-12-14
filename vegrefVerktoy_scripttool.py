import arcpy
import os
import requests
import regex as r

def ScriptTool(innDatasett, fraAttributt, tilAttributt, koordinatSystem):
    # Script execution code goes here
    arcpy.AddMessage("{0} - {1} - {2} - {3}".format(innDatasett, fraAttributt, tilAttributt, koordinatSystem))
    fc = innDatasett
    fcNavn = arcpy.Describe(fc).name
    testdata = ""
    nyDatasett = arcpy.management.CreateFeatureclass(arcpy.env.workspace, fcNavn + "_rute", "POLYLINE", fc,"DISABLED","DISABLED",koordinatSystem)
    arcpy.Append_management(fc, nyDatasett)
    arcpy.management.AddField(nyDatasett, "kommentar", 'TEXT')
    fields = ["OID@","SHAPE@", fraAttributt,tilAttributt, "Kommentar"]
    kommentar = []

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
            
            return koordinat

            
            
            
        elif r.status_code != 200:
            print('Not Found.')
            kommentar = "Kunne ikke hente vegsystemreferanse-koordinat"
            
            return "SKIP!!"
        
        


        
        

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
    whr = "OBJECTID < 30"
    with arcpy.da.UpdateCursor(nyDatasett, fields, whr) as updateCursor:
    # with arcpy.da.UpdateCursor(nyDatasett, fields) as updateCursor:  
        

        for index,row in enumerate(updateCursor):
            kommentar = "" 
            print(row)
            radPrint = "{0} {1} {2} - {3}".format(row[0], row[4], row[2], row[3])
            arcpy.AddMessage(radPrint)
            # print(u'{0}, {1}, {2}, {3}'.format(row[0], row[1], row[2], row[3]))
            
            # if index == 6: # There's gotta be a better way.
            #     break
            if index != 19: # There's gotta be a better way.
                    pass
            
            if row[2] is None or row[3] is None:
                print("Her e det ingenting!")
                kommentar = "Mangler enten fra eller til referanse"
                
                rad = [row[0],None,row[2], row[3], kommentar]
                testdata = [rad]
                arcpy.AddMessage(rad)
                updateCursor.updateRow(rad)
                
                continue
            
            pktFra = hentVegsysrefKorrd(row[2])
            # print("Punkt fra {}".format(pktFra))
            
            pktTil = hentVegsysrefKorrd(row[3])
            # print("Punkt til {}".format(pktTil))
            
            
            
            if pktTil == "SKIP!!" or pktFra == "SKIP!!":
                rad = [row[0],None,row[2], row[3], kommentar]
                testdata = [rad]
                print(rad)
                updateCursor.updateRow(rad)
                
            
                continue
            
            if pktTil != "SKIP!!" or pktFra != "SKIP!!":
                rute = hentRute(pktTil, pktFra)
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
                    arcpy.AddMessage("----------------------- || " + radPrint + "|| ------------------------------- \n\n\n ")
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
    
    ScriptTool(innDatasett, fraAttributt, tilAttributt, koordinatSystem)
    
    # Update derived parameter values using arcpy.SetParameter() or arcpy.SetParameterAsText()