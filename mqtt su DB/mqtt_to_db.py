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

        
# Impostazioni comunicazione MQTT 
MQTT_Broker = "[IP_Server_MQTT]" #questo e' il server, sara' quasi sicuramente l'IP del PC su cui stai facendo girare il sistema
MQTT_Port = 1883
Keep_Alive_Interval = 45
MQTT_Topic2 = "topicTemp"
MQTT_Topic1 = "topicCorrente"
percorsoDB = "/percorso/domotica.db"


# Sottoscrizione a tutti i topic dei vari sensori
def on_connect(mosq, obj, rc):
	mqttc.subscribe([(MQTT_Topic1, 0), (MQTT_Topic2, 0)])

       
# Salvare i dati in arrivo nella tabella corretta
def on_message(mosq, obj, msg):
        # un po' di debug a video
        print "Ricevuti dati MQTT ..."
        print "MQTT Topic: " + msg.topic  
        print "Payload: " + msg.payload

        connessione = None
        
        tabella = ""
        
        # a seconda del topic devo decidere cosa memorizzare
        # fre riferimento agli ID della tabella "Luoghi" del DB in uso
        if msg.topic == "topicTemp":
            luogo = "1"
            tabella = "Temperature"
            
        if msg.topic == "topicCorrente":
            luogo = 1
            tabella = "Corrente"
            
        if tabella == "Temperature":    
            try:
                connessione = sqlite3.connect(percorsoDB)
                
                cursore = connessione.cursor()
                # inserisco la lettura della temperatura
                cursore.execute("INSERT INTO Temperature (Luogo, Temp) VALUES (" + luogo + ", " + msg.payload + ");")
        
                
                print 'Ho registrato questo: zona ' + msg.topic + ' - Temperatura ' + msg.payload + '*C'
            
            except sqlite3.Error, e:
                return "Error %s:" % e.args[0]
            
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
                # inserisco la lettura della corrente
                cursore.execute("INSERT INTO Corrente (Luogo, Consumo) VALUES (" + str(luogo) + ", " + str(msg.payload) + ");")
        
                
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

mqttc = mqtt.Client()

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe

# Connessione al broker
mqttc.connect(MQTT_Broker, int(MQTT_Port), int(Keep_Alive_Interval))

# Non mi fermo mai...
mqttc.loop_forever()
