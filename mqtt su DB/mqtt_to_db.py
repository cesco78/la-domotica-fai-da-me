#!/usr/bin/env python2.7

# Questo sketch fa parte del progetto www.ladomoticafaidame.it
# Tutte le informazioni relative al progetto o allo schema dei 
# componenti puo' essere trovato sul sito.
# 
# Il progetto e' distribuito con licenza GPL v.3
# Puoi usare liberamente questo codice, puoi modificarlo
# a seconda delle tue necessita' e puoi distribuirlo.
# Devi mantenere la citazione dello sviluppatore e 
# devi distribuirlo con la stessa licenza.
# 
# Il progetto e' di Francesco Tucci
#  www.iltucci.com
#  twitter.com/cesco_78
#
# applicazione MQTT per ricevere i dati dei sensori e degli allarmi del sistema
# il DB e' in SQlite
# nome del DB: domotica.db
# accedere alla gestione del DB --> $ sqlite3 domodica.db
#
# Fare il backup del DB (non dimenticarsi di farlo!!)
# comando --> echo '.dump' | sqlite3 domotica.db > exportdb
#
# Versione del 26/12/2018

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import sqlite3
import time
import ConfigParser
import datetime

        
# Impostazioni comunicazione MQTT 
MQTT_Broker = "[IP_server]" #questo e' il server, sara' quasi sicuramente l'IP del PC su cui stai facendo girare il sistema
MQTT_Port = 1883
Keep_Alive_Interval = 45
MQTT_Topic2 = "topicDHTCamera"
MQTT_Topic1 = "topicSHTEsterno"
MQTT_Topic3 = "topicCorrente"
MQTT_Topic4 = "topicEinkRequest"
MQTT_Topic5 = "topicAcquario1"
MQTT_Topic6 = "topicBagno"
MQTT_Topic7 = "topicStudio"
percorsoDB = "/percorso/database.db"
statoConnessione = 0

# genero un timestamp per l'inserimento nel file di log all'inizio di ogni riga
# ritorna il timestamp nel formato dd-mm-aaaa hh:mm:ss
def adesso():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return st

# qualche nota sul file di log:
# - il timestamp nel formato dd-mm-aaaa hh:mm:ss messo all'inizio della riga e' generato dalla funzione adesso()
# - dopo il timestamp metto tre caratteri che riguardano il tipo si messaggio
#   0 = [INF] informazione
#   1 = [AVV] avviso
#   2 = [ERR] errore
# cosi' posso filtrare il log alla ricerca di errori senza vedere tutti i messaggi meno gravi
def logga(livello, messaggio):
    # apro il file di log in append
    log = open (ConfigSectionMap("Sistema")['log'], "a")
    
    # inizio mettendo il timestamp
    stringa = adesso()
    
    # aggiungo il livello di gravita'
    if livello == 0:
        stringa = stringa + " [INF]"
    elif livello == 1:
        stringa = stringa + " [AVV]"
    else:
        stringa = stringa + " [ERR]"
        
    # inserisco il messaggio
    stringa = stringa + " " + messaggio
    
    # lo scrivo nel file
    log.write(stringa + "\n")
    
    # chiudo il file di log
    log.close()
    
# funzione per la memorizzazione di tutti i parametri nel file di configrazione
# per poter accedere al parametro basta usare il comando
# x = ConfigSectionMap("nome_sezione")['nome_parametro']
# ritorna un array con tutti i valori della sezione richiesta
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

# Sottoscrizione a tutti i topic dei vari sensori
# su una scheda raspberry, questo ha funzionato, su un'altra no. Se nno va basta metterlo al fondo
#def on_connect(mosq, obj, rc):
#    
#    try: 
#        mqttc.subscribe([(MQTT_Topic1, 0), (MQTT_Topic2, 0), (MQTT_Topic3, 0), (MQTT_Topic4, 0), (MQTT_Topic5, 0), (MQTT_Topic6, 0), (MQTT_Topic7, 0)])
#        print ("sottoscritti i topic")
#    except:
#        print("qualcosa non va")
            
       
# Salvare i dati in arrivo nella tabella corretta
def on_message(mosq, obj, msg):
        # un po' di debug a video
        print "MQTT Data Received..."
        print "MQTT Topic: " + msg.topic  
        print "Data: " + msg.payload
        
        logga(0, "Dati MQTT letti: Topic: " + msg.topic + " - Dati: " + msg.payload)
        
        connessione = None
        
        tabella = ""
        
        # a seconda del topic devo decidere cosa memorizzare
        # fre riferimento agli ID della tabella "Luoghi" del DB in uso
        if msg.topic == "topicDHTCamera":
            luogo = "1"
            tabella = "Temperature"
            
        if msg.topic == "topicSHTEsterno":
            luogo = "2"
            tabella = "Temperature"

        if msg.topic == "topicAcquario1":
            luogo = "9"
            tabella = "Temperature"

        if msg.topic == "topicBagno":
            luogo = "7"
            tabella = "Temperature_new" #la procedura della temperatura NEW gestisce anche la batteria
            print("questo e' il bagno")

        if msg.topic == "topicStudio":
            luogo = "6"
            tabella = "Temperature_new" #la procedura della temperatura NEW gestisce anche la batteria
            print("questo e' lo studio")
            
        if msg.topic == "topicCorrente":
            luogo = 1
            tabella = "Corrente"
            
        if msg.topic == "topicEinkRequest":
            print 'ehi, devo fornirti i dati dei sensori per il display'
            logga(0, "Richiesta dati per il display")
            try:
                payload = ""
                connessione = sqlite3.connect(percorsoDB)
                cursore = connessione.cursor()
                
                # cerco il consumo di oggi
                cursore.execute("select strftime('%d/%m', the_day), SUM(consumo_medio), strftime('%w', the_day) from ( select the_day, the_hour, AVG(the_count) as consumo_medio from ( select date(timestamp) as the_day, strftime('%H', timestamp) as the_hour, avg(Consumo) as the_count from Corrente group by the_day, the_hour) group by the_day, The_hour) group by the_day order by the_day desc limit 1;")
                righe = cursore.fetchall()
                for row in righe:
                    consumoOggi = int(row[1])
                
                payload = payload + str(consumoOggi) + "W&"

                # generazione del cursore per i luoghi
                cursore_luoghi = connessione.cursor()
                
                # leggo l'elenco dei luoghi
                cursore_luoghi.execute("SELECT ID, Descrizione FROM Luoghi;")
                
                # per ogni luogo estraggo le temperature
                righe_luoghi = cursore_luoghi.fetchall()
                
                # estraggo i dati dei vari luoghi a partire dai risultati della query precedente
                for row_luoghi in righe_luoghi:
                    # variabile per verficare se ho trovato o meno dati della stanza
                    stanza_con_dati = 0
                
                    # leggo l'ultimo valore memorizzato
                    cursore.execute("SELECT ID, strftime('%H:%M', Timestamp, 'localtime'), Luogo, Temp, Umid FROM Temperature WHERE Luogo = " + str(row_luoghi[0]) + " ORDER BY ID DESC LIMIT 1;")
                    righe_ultima = cursore.fetchall()
                    
                    # compongo il messaggio
                    for row in righe_ultima:
                        payload = payload + str(row_luoghi[1]) + "&" + str(row[3]) + "&"

            except sqlite3.Error, e:
                logga(2, "Errore SQL MQTT ricerca dati per display - Error %s:" % e.args[0])
                return "Error %s:" % e.args[0]
            
            finally:
                if connessione:
                    try:
                        connessione.commit()
                        connessione.close()
                    except sqlite3.Error, e:
                        logga(2, "Errore SQL MQTT commit per display - Error %s:" % e.args[0])
                        return "Error %s:" % e.args[0]
            print payload
            logga(0, "Dati trasmessi al display: " + e.args[0])
            publish.single("topicEinkPrint", payload, hostname="10.99.99.170")
            
        # questa funzione importa nella tabella la sola lettura delle temperatura (tipo quella dell'acquario)
        if tabella == "Temperature":    
            try:
                connessione = sqlite3.connect(percorsoDB)
                
                cursore = connessione.cursor()
                # inserisco la lettura della temperatura
                cursore.execute("INSERT INTO Temperature (Luogo, Temp) VALUES (" + luogo + ", " + msg.payload + ");")
        
                logga(0, "Lettura sensore MQTT: zona " + msg.topic + " - Temperatura " + msg.payload + "*C")
                print 'Ho registrato questo: zona ' + msg.topic + ' - Temperatura ' + msg.payload + '*C'
            
            except sqlite3.Error, e:
                logga(2, "Errore SQL MQTT registrazione dati sensore - Error %s:" % e.args[0])
                return "Error %s:" % e.args[0]
            
            finally:
                if connessione:
                    try:
                        connessione.commit()
                        connessione.close()
                    except sqlite3.Error, e:
                        logga(2, "Errore SQL MQTT commit per registrazione sensore - Error %s:" % e.args[0])
                        return "Error %s:" % e.args[0]

        #questa gestione dell'arrivo della temperatura gestisce anche l'umido e la batteria
        if tabella == "Temperature_new":    
            try:
                connessione = sqlite3.connect(percorsoDB)
                
                # faccio lo split della stringa che arriva dalla scheda, il formato e' questo:
                # "00,00 # 00,00 # 0,00" dove
                # - il primo numero e' la temperatura in gradi celsius
                # - il secodo numero e' l'umidita' in percentuale
                # - il terzo numero e' la tensione della batteria
                #
                # da prove sperimentali, sotto i 2,55V le letture diventano irreali e mostrano i dati di minimo e massimo
                # del sensore. Quindi se la temperatura e' -45 o 130 e l'umidita' e' 100 la batteria e' troppo bassa
                
                # faccio lo split della stringa
                t,h,v = msg.payload.split("#")
                
                # tolgo gli spazi daventi e dietro
                t = t.strip()
                h = h.strip()
                v = v.strip()
                
                cursore = connessione.cursor()
                # inserisco la lettura dei dati nella tabella
                cursore.execute("INSERT INTO Temperature (Luogo, Temp, Umid, Vbatt) VALUES (" + luogo + ", " + t + ", " + h + ", " + v +");") 
                
                logga(0, 'Lettura MQTT: zona ' + msg.topic + ' - Temperatura ' + t + '*C - Umid ' + h + '% - Batteria ' + v + 'V')
                print 'Ho registrato questo: zona ' + msg.topic + ' - Temperatura ' + t + '*C - Umid ' + h + '% - Batteria ' + v + 'V' 
            
            except sqlite3.Error, e:
                logga(2, "Errore SQL MQTT registrazione dati sensore - Error %s:" % e.args[0])
                return "Error %s:" % e.args[0]
            
            except Exception as e:
                print("qualcosa non va")
                print(e)
            
            finally:
                if connessione:
                    try:
                        connessione.commit()
                        connessione.close()
                    except sqlite3.Error, e:
                        return "Error %s:" % e.args[0]        
        
        if tabella == "Corrente":
            try:
                connessione = sqlite3.connect(percorsoDB)
                
                cursore = connessione.cursor()
                # inserisco la lettura della temperatura
                cursore.execute("INSERT INTO Corrente (Luogo, Consumo) VALUES (" + str(luogo) + ", " + str(msg.payload) + ");")
        
                logga(0, 'Ho registrato questo: zona ' + msg.topic + ' - Consumo ' + msg.payload + 'Watt')
                print 'Ho registrato questo: zona ' + msg.topic + ' - Consumo ' + msg.payload + 'Watt'
            
            except sqlite3.Error, e:
                return "Error %s:" % e.args[0]
            
            finally:
                if connessione:
                    try:
                        connessione.commit()
                        connessione.close()
                    except sqlite3.Error, e:
                        return "Error %s:" % e.args[0]


def on_subscribe(mosq, obj, mid, granted_qos):
    pass

# leggo il file di configurazione per recuparare tutti i parametri di funzionamento del sistema
# la cosa migliore sarebbe avere questo file in /etc/tvcc.conf per rispettare le convenzioni in linux
# io lo tengo nella cartella dove lavoro per questione di comodita'
Config = ConfigParser.ConfigParser()
Config.read("/percorso/tvcc.conf")

mqttc = mqtt.Client()
print("creato client")
logga(0, "Creato client MQTT")



# Callback per gli eventi
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe

# Connessione al broker MQTT
# non si avvia fino a quando non riesce a connettersi
while statoConnessione == 0:
    try:
        mqttc.connect(MQTT_Broker, int(MQTT_Port), int(Keep_Alive_Interval))
        print("connesso")
        logga(0, "Connesso al broker MQTT")
        statoConnessione = 1
    except:
        print("Problema di connessione")
        logga(2, "Impossibile connettersi al broker MQTT")
        statoConnessione = 0
        time.sleep(10)
        
    try: 
        mqttc.subscribe([(MQTT_Topic1, 0), (MQTT_Topic2, 0), (MQTT_Topic3, 0), (MQTT_Topic4, 0), (MQTT_Topic5, 0), (MQTT_Topic6, 0), (MQTT_Topic7, 0)])
        print ("sottoscritti i topic")
        logga(0, "Sottoscrizione topic OK")
        statoConnessione = 1
    except:
        print("qualcosa non va")
        logga(2, "Sottoscrizione topic OK")
        statoConnessione = 0
        time.sleep(10)


# Aspetta i dati per sempre
mqttc.loop_forever()








