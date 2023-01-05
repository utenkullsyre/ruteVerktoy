import arcpy
import os
import requests
import regex as r
from datetime import datetime

# Funksjon som inneholder all koden som skal kjøres
def ScriptTool(innDatasett, fraAttributt, tilAttributt, dato, koordinatSystem, query):



    # Henter prosjekt-objektet
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Henter map-objektet
    mp = aprx.activeMap
    #Setter opp env parametre
    arcpy.env.overwriteOutput = True # Skriver over gammelt script-resultat
    #arcpy.AddMessage(dato)
    
    #Setter opp scriptvariabler
    fc = innDatasett
    fcNavn = arcpy.Describe(fc).name

    dato_obj = datetime.strptime(dato, "%d.%m.%Y")
    
    #arcpy.AddMessage("{}-{}-{}".format(dato_obj.day,dato_obj.month,dato_obj.year))
    
    #Lager nytt datasett, laster over data fra input-data og legger til nydatasett i kartet
    nyDatasett = arcpy.management.CreateFeatureclass(arcpy.env.workspace, fcNavn + "_rute", "POLYLINE", fc,"DISABLED","DISABLED",koordinatSystem)
    #Laster inn data fra input-datasett til nydatasett
    arcpy.Append_management(fc, nyDatasett)
    # Legger til et felt som skal holde kommentarer
    arcpy.management.AddField(nyDatasett, "kommentar", 'TEXT')
    # Legger til nydatasettet til det aktive kartet
    mp.addDataFromPath(nyDatasett)
    
    #Legger relevante felt i liste som skal brukes i UpdateCursor
    fields = ["OID@","SHAPE@", fraAttributt,tilAttributt, "Kommentar"]
    
    #Kommentar-variabel som skal legges inn i rad
    kommentar = ""

    #Funksjon for å hente ned koordinater for vegsystemreferanse-posisjon
    def hentVegsysrefKorrd(vegsystemReferanse, dato):
        #Bygger tidspunkt parameter
        
        tid = "&tidspunkt={}-{:02d}-{:02d}".format(dato_obj.year,dato_obj.month,dato_obj.day)
        #Lager url som skal sendes
        urlKoord = "https://nvdbapiles-v3.atlas.vegvesen.no/veg?vegsystemreferanse=" + str(vegsystemReferanse) + tid
        
        #Viktig med X-Client header til NVDB-APIet
        headers = {'X-Client':"ArcGis Pro verktøy: Hent rute (tobors)"}

        #Sender request
        r = requests.get(urlKoord, headers=headers)
        
        #Sjekker om responsen ble vellykket
        if r.status_code == 200:
            #Lagrer resultatet som json
            resultat =  r.json()
            
            #Henter ut wkt-streng fra resultatet
            pktWKT = resultat['geometri']['wkt']
            
            #Plukker ut kun koordinatene fra WKT-streng
            koordinat = pktWKT[pktWKT.find("(")+1:pktWKT.find(")")].split(" ")[0:2]
            
            #Sender tilbake koordinatene
            return [koordinat]

            
            
        # Fanger opp om request'n feilet
        elif r.status_code != 200:
            kommentar = "Kunne ikke hente vegsystemreferanse-koordinat"
            
            # Sender ut feilkode og feil-tekst fra resultat
            return ["Error", r.text]
        
        


        
        
    # Funksjon for å laste ned linje-geometri fra ruteplanleggeren
    def hentRute(fraKoord, tilKoord):
        
        # Setter opp url til tjeneste, dette er den offentlige med begrensninger
        urlRute = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v2_0/open/routingservice?"
        
        # Legger til fra / til koordinatene i 'stops-egenskapen'
        PARAMS = {
            'stops':";".join([",".join(fraKoord),",".join(tilKoord)]),
            'returnDirections':"false",
            'returnGeometry':'true',
            'format':'json'
        }
        
        # Legger inn X-Client header slik at NVDB-api'et kan kjenne igjen 
        headers = {'X-Client':"ArcGis Pro verktøy: Hent rute (tobors)"}
        
        # Logger fremgang
        arcpy.AddMessage(" --> sender spørring til ruteplanleggeren\n")
        arcpy.AddMessage(" ---> koordinatpar: {}".format(PARAMS["stops"]))
        
        # Sender spørring etter rute
        r = requests.get(url = urlRute, params = PARAMS, headers=headers)
        
        # Laster inn resultat som json
        results = r.json()
        
        # Henter koordinatene for linje
        ruteGeometri = results['routes']['features'][0]['geometry']['paths']
        
        # Deklarerer en variabel som skal holde alle linjestykkene, dette i tilfelle det er flere enn en linje
        features = []
        
        # Logging for loggingens skyld
        arcpy.AddMessage(" --> lager geometri av resultatet\n")
        
        # Itererer gjennom linjesegmenter returnert fra rutetjenesten
        for feature in ruteGeometri:
            # Lager et polylinjeobjekt og legger dette til lista
            linje = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for coords in feature]),koordinatSystem)
            
            # polylinje = linje

            # Legger linja til lista  
            features.append(
                linje
                )
        
        return  features

    # Lager en updatecursor for å iterere og oppdatere radene i det nye datasettet
    with arcpy.da.UpdateCursor(nyDatasett, fields, query) as updateCursor:        

        # Itererer over radene i updatecursor-objektet
        for index,row in enumerate(updateCursor):
            
            # Deklarerer en kommentar-variabel som skal brukes senere 
            kommentar = "" 
            
            # Logger at scriptet har begynt med denne raden
            arcpy.AddMessage("\n\n-----------------------------------------------\nForsøker å laste ned geometri for ID: {}  -- Pkt fra: {} | Pkt til: {}\n".format(row[0], row[2], row[3]))
            
            #  Sjekker om det mangler vegsystemreferanser
            if row[2] is None or row[3] is None:
                # Oppdaterer kommentar-variabel med feilmelding
                kommentar = "FEIL: Mangler enten fra eller til referanse"
                #Legger inn data som skal lagres tilbake i raden
                rad = [row[0],None,row[2], row[3], kommentar]
                # Logger feilmelding 
                arcpy.AddWarning(" !!  fant ikke fra eller til referanse, går til neste rad !! \n\n")
                # Lagrer dataene i raden
                updateCursor.updateRow(rad)
                
                # Avslutter denne iterasjonsrunden og hopper til neste rad
                continue
            
            # Logger fremgang
            arcpy.AddMessage(" --> henter koordinater for vegsystemreferanser\n")
            
            # Henter koordinater for pktFra og pktTil
            pktFra = hentVegsysrefKorrd(row[2], dato)            
            pktTil = hentVegsysrefKorrd(row[3], dato)            
            
            # Sjekker om hentVegsysrefKoord funksjon har returnert en feil, og bruker en veldig knotete og dum metodikk for å løse dette på
            if pktTil[0] == "Error" or pktFra[0] == "Error":
                manglerKoordinat = []
                responseData = []
                
                if pktFra[0] == "Error":
                    manglerKoordinat.append("Punkt fra")
                    responseData.append("Pkt fra responsedata: \n{}".format(pktFra[1]))
                if pktTil[0] == "Error":
                    manglerKoordinat.append("Pkt til")
                    responseData.append("Pkt til responsedata: \n{}".format(pktTil[1]))
                    
                # Oppdaterer kommentar med feilmelding, denne lagres på "kommentar"-egenskap i raden
                kommentar = "FEIL: Fant ikke koordinat på: {}".format(",".join(manglerKoordinat))
                
                rad = [row[0],None,row[2], row[3], kommentar]

                # Logger for å vise hvilket punkt som feilet
                arcpy.AddWarning(" !! Objekt med ID {}: {} !! \n{}\n\n".format(row[0], kommentar,",".join(responseData)))
                
                # Lagrer data til rad
                updateCursor.updateRow(rad)
                
            
                continue
            
            
            # Hvis alt gått bra så langt, prøver scriptet å hente en rute
            if pktTil[0] != "Error" or pktFra[0] != "Error":
                
                # Kjører hentRute funksjon
                rute = hentRute(pktTil[0], pktFra[0])

                # Lager en iterasjon i tilfelle rute-funksjon har levert mer enn en geometri. 
                for r in rute:
                    # Oppdaterer kommentar som skal lagres på rad
                    kommentar = "Linje-geometri hentet ned"
                    # Oppdaterer rad-info
                    rad = [row[0],r,row[2], row[3], kommentar]
                    # Legger til logging for å vise fremgang
                    arcpy.AddMessage(" * Generert linje-geometri for objekt med id {} * \n\n".format(row[0]))
                    # Lagrer rad-data
                    updateCursor.updateRow(rad)

    return

# Python duppeditt for å kunne kjøre verktøyet
if __name__ == '__main__':

    # Verktøy-parametre satt av bruker hentes ned med GetParameter or GetParameterAsText
    innDatasett = arcpy.GetParameterAsText(0)
    fraAttributt = arcpy.GetParameterAsText(2)
    tilAttributt = arcpy.GetParameterAsText(3)
    dato = arcpy.GetParameterAsText(4)
    koordinatSystem = arcpy.GetParameterAsText(5)
    query = arcpy.GetParameterAsText(6)
    
    # Kjører verktøyet
    ScriptTool(innDatasett, fraAttributt, tilAttributt, dato, koordinatSystem, query)
    
    
    # Her kan du sende tilbake informasjon til verktøyet ved å bruke arcpy.SetParameter() or arcpy.SetParameterAsText()