#!/usr/bin/env python3

#
# Visualizzare le informazioni del progetto www.ladomoticafaidamie.it in un modo semplice e immediato
# un progetto di Francesco Tucci (https://www.iltucci.com)
# versione 1.0 del 22/04/2020 (durante la quarantena per il Coronavirus)
#
# materiale necessario:
# . Raspberry Pi (una versione qualsiasi, basta che abbia il GPIO da 40 pin)
# . Scheda microSD
# . ALimentatore per il Raspberry
# . display Inky-wHat di Pimoroni https://shop.pimoroni.com/products/inky-what?variant=21214020436051
#
# Per preparare la scheda e' necessario fare riferimento all'articolo esplicativo sul blog:
# tutti i "print" sparsi nel codice sono essenzialmente per debug, e una volta finito il progetto possono essere tolti.

# sezione di importazione delle librerie
# --------------------------------------#

# libreria per la gestione del display e-ink
# $ sudo pip3 install inky
from inky import InkyWHAT

# libreria per poter disegnare e scrivere sul display
# si installa con un sacco di librerie a corredo
# https://pillow.readthedocs.io/en/latest/installation.html 
from PIL import Image, ImageDraw, ImageFont

# per avere le date in Italiano
import locale

# questa libreria mi serve per avere le effemeridi
import ephem

# la mia libreri con le varie funzioni standard
import funzioni_tucci

# gestione delle date
from datetime import datetime
from datetime import date
import datetime as dt
import time

# gestione delle festività
import holidays

# manipolare il DB SQLite3
import sqlite3

# richieste http per scaricare i dati da internet,
# che siano API con un bel JSON o una pagina web generaica da analizzare
import requests

# libreria per eseguire comandi del sistema operativo
# e usarne poi i risultati.
import os

# gestione degli array
from array import *

# funzione che tronca i decimali
# - n: il numero da analizzare
# - decimal: la quantit' di decimali da tenere
# Restituisce un numero con i decimali richieste
def truncate(n, decimali=0):
    m = 10 ** decimali
    return int(n * m) / m

# funzione per allineare il grafico a barre a seconda dei volri minimi e massimi
# che passo, così posso avere un grafico indicativo senza impazzire con il calcolo delle altezze
# il valore minimo sarà 1 pixerl il massimo 20, la scala è lineare.
# - consumo: il valore da assegnare alla barretta
# - massima: valore massimo della serie
# - minima: valore minimo della serie
# Restituisce un valore numerico cmopreso tra 1 e 20
def altezzaGrafico (consumo, massima, minima):
  diff_consumo = consumo - minima
  percentuale = diff_consumo / (massima-minima)
  valoreGrafico = percentuale * (20-1) + 1
  if valoreGrafico < 0:
    valoreGrafico = 0
  return round(valoreGrafico,0)


# sezione di inizializzazione dei componenti
# ------------------------------------------ #

# imposta il locale in Italiano
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

# il percorso del font da usare
font_TTF = "/home/pi/what/Arial.ttf"

# inizializzare il display
# il mio è quello solo B/N, purtroppo
inkywhat = InkyWHAT('black')

# si definisce il buffer dentro il quale scrivere
# tutto il programma scriverà nel buffer, che verrà poi passato al display solo alla fine
img = Image.new("P", (inkywhat.WIDTH, inkywhat.HEIGHT))
draw = ImageDraw.Draw(img)


# variabili da impostare prima di avviare il programma
# ---------------------------------------------------- #

# percorso del DB SQLite locale
db_sqlite_locale = 'XXX'

# percorso del DB SQLite remoto (quello montato con SSHFS prima dell'avvio dello script)
db_sqlite_remoto = 'XXX'

# IP del router da controllare
ip_router = 'XXX'

# indirizzo SNMP porta WAN per traffico upload
iso_wan_up = 'iso.XXX'

# indirizzo SNMP porta WAN per traffico download
iso_wan_down = 'iso.XXX'

# latitudine e longitudine della città per le effemeridi
latitudine = 'xx.xx'
longitudine = 'xx.xx'

# dati per openweathermap
owm_api = 'xxx'
owm_id_city = 'xxx' #la lista delle città si trova qui: http://bulk.openweathermap.org/sample/

# cosa scrivere e disegnare
# ------------------------- #

# prima di ogni cosa disegno tutto lo schema dei rettangolini,
# con i titoli e le posizioni corrette.
# La posizione è calcolata tutta a mano, ma in una prossima versione conto di fare
# una funzione così da passare le dimensioni e il titolo e lei fa tutto.

# i font che verranno usati.
font_11 = ImageFont.truetype(font_TTF, 11)
font_12 = ImageFont.truetype(font_TTF, 12)
font_22 = ImageFont.truetype(font_TTF, 22)

# cornice larga 1px intorno al display
draw.rectangle([(0,0), (399, 299)], outline=inkywhat.BLACK, width=1)

# rettangolo dove va messo il calendario
draw.rectangle([(10,10), (139, 199)], outline=inkywhat.BLACK, width=1)

# rettangolo dove andra' scritto in negativo il giorno della settimana
draw.rectangle([(10,10), (139, 30)], fill= inkywhat.BLACK, outline=inkywhat.BLACK, width=1)

# rettangolo dove andra' scritto in negativo il mese
draw.rectangle([(10,160), (139, 180)], fill= inkywhat.BLACK, outline=inkywhat.BLACK, width=1)

# rettangoli per il meteo
draw.rectangle([(10,199), (75, 244)], outline=inkywhat.BLACK, width=1)
draw.rectangle([(75,199), (139, 244)], outline=inkywhat.BLACK, width=1)
draw.text((12,200), "Oggi", fill=inkywhat.BLACK, font=font_11)
draw.text((77,200), "Domani", fill=inkywhat.BLACK, font=font_11)



# rettangoli dove andranno messe le effemeridi
draw.rectangle([(149,10), (209, 49)], outline=inkywhat.BLACK, width=1)
draw.rectangle([(209,10), (269, 49)], outline=inkywhat.BLACK, width=1)
font_effemeridi = ImageFont.truetype(font_TTF, 11)
draw.text((166,11), "Alba", fill=inkywhat.BLACK, font=font_effemeridi)
draw.text((215,11), "Tramonto", fill=inkywhat.BLACK, font=font_effemeridi)

# rettangolo dove ci metto i PM10
draw.rectangle([(149,49), (269, 88)], outline=inkywhat.BLACK, width=1)
draw.text((155,50), "PM10 (ieri e storico)", fill=inkywhat.BLACK, font=font_effemeridi)


# rettangoli con le temperature dei vari sensori interni
draw.rectangle([(149,88), (209, 127)], outline=inkywhat.BLACK, width=1)
draw.text((155,89), "Sala", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(209,88), (269, 127)], outline=inkywhat.BLACK, width=1)
draw.text((215,89), "Studio", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(149,127), (209, 166)], outline=inkywhat.BLACK, width=1)
draw.text((155,128), "Bagno", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(209,127), (269, 166)], outline=inkywhat.BLACK, width=1)
draw.text((215,128), "Camera", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(149,166), (209, 205)], outline=inkywhat.BLACK, width=1)
draw.text((155,167), "Cucina", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(149,205), (209, 244)], outline=inkywhat.BLACK, width=1)
draw.text((155,206), "Pesci 30l", fill=inkywhat.BLACK, font=font_effemeridi)
draw.rectangle([(209,205), (269, 244)], outline=inkywhat.BLACK, width=1)
draw.text((215,206), "Pesci 90l", fill=inkywhat.BLACK, font=font_effemeridi)

# rettangolo con la temperatura esterna di Arpa
draw.rectangle([(209,166), (269, 205)], outline=inkywhat.BLACK, width=1)
draw.rectangle([(209,166), (269, 178)], fill= inkywhat.BLACK, outline=inkywhat.BLACK, width=1)
draw.text((215,167), "Temp. Ext", fill=inkywhat.WHITE, font=font_effemeridi)

# rettangolo lungo con il consumo in Wh su base giornaliera
draw.rectangle([(269,10), (389, 49)], outline=inkywhat.BLACK, width=1)
draw.text((275,11), "Consumo corrente oggi", fill=inkywhat.BLACK, font=font_11)

#rettangoli lungohi con i grafici dei consumi 
draw.rectangle([(269,49), (389, 88)], outline=inkywhat.BLACK, width=1)
draw.text((275,50), "30gg di consumi", fill=inkywhat.BLACK, font=font_11)
draw.rectangle([(269,88), (389, 127)], outline=inkywhat.BLACK, width=1)
draw.text((275,89), "Consumo corrente 24h", fill=inkywhat.BLACK, font=font_11)

# rettangoli per il consumo dei dati
draw.rectangle([(269,127), (389, 166)], outline=inkywhat.BLACK, width=1)
draw.text((275,128), "Up/down oggi [GB]", fill=inkywhat.BLACK, font=font_11)
draw.rectangle([(269,166), (389, 205)], outline=inkywhat.BLACK, width=1)
draw.text((275,167), "Upload in 24h", fill=inkywhat.BLACK, font=font_11)
draw.rectangle([(269,205), (389, 244)], outline=inkywhat.BLACK, width=1)
draw.text((275,232), "Download in 24h", fill=inkywhat.BLACK, font=font_11)

# le due righe in fondo con gli eventi di oggi e di domani
draw.rectangle([(0,259), (399, 279)], outline=inkywhat.BLACK, width=1)
draw.rectangle([(0,279), (399, 299)], outline=inkywhat.BLACK, width=1)
draw.rectangle([(70,259), (399, 279)], fill= inkywhat.BLACK, outline=inkywhat.WHITE, width=1)
draw.rectangle([(70,279), (399, 299)], fill= inkywhat.BLACK, outline=inkywhat.WHITE, width=1)
font_eventi = ImageFont.truetype(font_TTF, 18)
draw.text((5,259), "Oggi", fill=inkywhat.BLACK, font=font_eventi)
draw.text((5,279), "Domani", fill=inkywhat.BLACK, font=font_eventi)






# poi metto i contenuti
# ---------------------#

# il giorno della settimana
# estraggo il giorno della settimana di oggi e lo faccio tutto in maiuscolo
# visto che i giorni sono tutti di lunghezza diversa, lo posiziono al centro del suo rettangolo
giorno_settimana = datetime.now().strftime("%A").upper()
print("oggi è " + giorno_settimana)
font_giorno = ImageFont.truetype(font_TTF, 18)
lunghezza_giorno, altezza_giorno = font_giorno.getsize(giorno_settimana)
print("dimensioni testo del giorno della settimana: " + str(lunghezza_giorno) + " " + str(altezza_giorno))
draw.text((72-(lunghezza_giorno/2),11), giorno_settimana, fill=inkywhat.WHITE, font=font_giorno)

# il giorno del mese
giorno_mese = datetime.now().strftime("%d")
font_giorno_mese = ImageFont.truetype(font_TTF, 110)
lunghezza_giorno_mese, altezza_giorno_mese = font_giorno_mese.getsize(giorno_mese)
draw.text((72-(lunghezza_giorno_mese/2),35), giorno_mese, fill=inkywhat.BLACK, font=font_giorno_mese)

# il mese
mese = datetime.now().strftime("%B").upper()
font_mese = ImageFont.truetype(font_TTF, 18)
lunghezza_mese, altezza_mese = font_mese.getsize(mese)
print("lunghezza testo del mese: " + str(lunghezza_mese) + " " + str(altezza_mese))
draw.text((72-(lunghezza_mese/2),161), mese, fill=inkywhat.WHITE, font=font_giorno)

# la settimana
settimana = datetime.now().strftime("%U")
font_settimana = ImageFont.truetype(font_TTF, 12)
draw.text((12,183), "Sett: " + settimana, fill=inkywhat.BLACK, font=font_settimana)

# giorno attuale e quanti ne mancano alla fine dell'anno
num_giorno = datetime.now().strftime("%j")
giorni_alla_fine = 365-int(num_giorno)
stringa_giorni = num_giorno + "-" + str(giorni_alla_fine)
draw.text((85,183), stringa_giorni, fill=inkywhat.BLACK, font=font_settimana)

# le effemeridi del sole
# uso la libreria ephem per recuperare le effemerdi del sole
# link alla documentazione
# 1 - http://rhodesmill.org/pyephem/quick.html#phases-of-the-moon
# 2 - http://rhodesmill.org/pyephem/date.html
# i dati inseriti qui sono relativi alla città di Torino, è necessario mettere quelli della propria città
torino = ephem.Observer()
torino.pressure = 0
torino.lat, torino.lon = latitudine, longitudine
torino.horizon = '-0:34'
torino.date = funzioni_tucci.adesso_mezzanotte()
sole_sorge = ephem.localtime(torino.next_rising(ephem.Sun())).strftime('%H:%M')
sole_tramonta = ephem.localtime(torino.next_setting(ephem.Sun())).strftime('%H:%M')
print("Alba e tramonto del sole " + sole_sorge +  " " + sole_tramonta)
font_effemeridi_orario = ImageFont.truetype(font_TTF, 22)
draw.text((152,24), sole_sorge, fill=inkywhat.BLACK, font=font_effemeridi_orario)
draw.text((212,24), sole_tramonta, fill=inkywhat.BLACK, font=font_effemeridi_orario)

# i PM10 presi dal sito di Arpa Piemonte
# facendo scraping della pagina web

# prima mi serve la data in giorno, mese e anno
pm10_gg = (datetime.now() - dt.timedelta(days=1)).strftime('%d')
pm10_mm = (datetime.now() - dt.timedelta(days=1)).strftime('%m')
pm10_aaaa = (datetime.now() - dt.timedelta(days=1)).strftime('%Y')

link_arpa_piemonte = 'http://www.sistemapiemonte.it/ambiente/srqa/consultadati_prov.shtml?index=1&cip=001&comune=001272&tipo=SP&parametro=POL_PM10&dd=' + str(pm10_gg) +'&mm=' + str(pm10_mm) + '&yyyy=' + str(pm10_aaaa)
print("link Arpa: " + link_arpa_piemonte)
# apro la pagina di Arpa Piemonte con i parametri impostati
connessione = 0
font_pm10_valore = ImageFont.truetype(font_TTF, 22)
try: 
    r = requests.get(link_arpa_piemonte)
    connessione = 1
except:
    print("NO Internet")

if (connessione == 1):
    # nel sorgente cerco la parola chiave
    carattere_ricerca = r.text.find('Concentrazione:')
    # estraggo il valore
    valore_pm10 = r.text[carattere_ricerca+16:carattere_ricerca+19].strip()
    if valore_pm10.isnumeric():
        draw.text((165,64), valore_pm10, fill=inkywhat.BLACK, font=font_pm10_valore)
        # se ho il valore lo posso scrivere nel DB
        # prima controllo se per questa data l'ho gia scritto
        connessione = sqlite3.connect(db_sqlite_remoto)
        cursore = connessione.cursor()
        print("Query ricerca valore PM10: " + "SELECT * FROM PM10 WHERE Data = '" + (datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d') +"';")
        cursore.execute("SELECT * FROM PM10 WHERE Data = '" + (datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d') +"';")
        if cursore.fetchone() == None:
            # non c'è il valore di oggi, allora lo inserisco
            print("Query insert valore: " + "INSERT INTO PM10 (Data, Valore) VALUES ('" + (datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d') + "', " + valore_pm10 + ");")
            cursore.execute("INSERT INTO PM10 (Data, Valore) VALUES ('" + (datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d') + "', " + valore_pm10 + ");")
        connessione.commit()
        connessione.close()
    else:
        draw.text((155,64), "n.d.", fill=inkywhat.BLACK, font=font_pm10_valore)
else:
    draw.text((155,64), "Conn", fill=inkywhat.BLACK, font=font_pm10_valore)
    
# La temperatura presi dal sito di Arpa Piemonte
# facendo scraping della pagina web, relativa alla centralina di via Reiss Romoli a Torino

link_arpa_piemonte_temp = 'http://webgis.arpa.piemonte.it//bancadatimeteo/php/pagina_meteo.php?CODTOT=001272905'
print("link Arpa: " + link_arpa_piemonte_temp)
# apro la pagina di Arpa Piemonte con i parametri impostati
connessione = 0
font_temp_ext_valore = ImageFont.truetype(font_TTF, 22)
try: 
    r = requests.get(link_arpa_piemonte_temp)
    connessione = 1
except:
    print("NO Internet")

if (connessione == 1):
    # nel sorgente cerco la parola chiave
    carattere_ricerca = r.text.find('TEMPERATURA DELL')
    # estraggo il valore
    valore_temp_ext = r.text[carattere_ricerca+46:carattere_ricerca+51].strip()
    valore_temp_ext = valore_temp_ext.replace("°", "")
    valore_temp_ext = valore_temp_ext.replace("C", "")
    valore_temp_ext = valore_temp_ext.replace(" ", "")
    print("Temperatura: " + valore_temp_ext)
    print("lettura web: " + r.text[carattere_ricerca:carattere_ricerca+51])
    draw.text((216,179), valore_temp_ext+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore)

    
    # gia' che ci sono scrivo la temperatura nel DB (cosi' non mi serve più il sensore sul balcone)
    connessione = sqlite3.connect(db_sqlite_remoto)
    cursore = connessione.cursor()    
    cursore.execute("INSERT INTO Temperature (Luogo, Temp) VALUES (5, " + valore_temp_ext + ");")
    connessione.commit()
    connessione.close()
    
else:
    draw.text((211,64), "Conn", fill=inkywhat.BLACK, font=font_temp_ext_valore)


# festività di oggi con la libreria
giorni_festivi = holidays.IT()
oggi_festa = giorni_festivi.get(funzioni_tucci.oggi())
font_festa = ImageFont.truetype(font_TTF, 14)
print("Festività di oggi " + str(oggi_festa))
festa_da_libreria =""
if str(oggi_festa) != "None":
    festa_da_libreria = str(oggi_festa)


# gli eventi da DB
# la data di oggi, senza anno
data_corta = funzioni_tucci.oggi_breve()
print("Data breve oggi: " + str(data_corta))
# mi collego al DB
connessione = sqlite3.connect(db_sqlite_locale)
cursore = connessione.cursor()
# cerco gli eventi di oggi
cursore.execute("SELECT * FROM Eventi WHERE Data = '" + str(data_corta) + "';")
print("SELECT * FROM Eventi WHERE Data = '" + str(data_corta) + "';")
righe = cursore.fetchall()
# estraggo gli eventi e li scrivo nel posto giusto sul display
# tanto è una sola riga
festa_da_db =""
for row in righe:
    print("Trovato evento oggi")
    festa_da_db = str(row[1])
    

draw.text((75,259), festa_da_db + " " + festa_da_libreria, fill=inkywhat.WHITE, font=font_eventi)    

# festività di domani con la libreria
giorni_festivi = holidays.IT()
domani_festa = giorni_festivi.get(funzioni_tucci.domani_breve())
font_festa = ImageFont.truetype(font_TTF, 14)
print("Festività di domani " + str(oggi_festa))
festa_da_libreria_domani =""
if str(domani_festa) != "None":
    festa_da_libreria_domani= str(oggi_festa)

# cerco gli eventi di domani
data_corta = funzioni_tucci.domani_breve()
cursore.execute("SELECT * FROM Eventi WHERE Data = '" + str(data_corta) + "';")
print("SELECT * FROM Eventi WHERE Data = '" + str(data_corta) + "';")
righe = cursore.fetchall()

# estraggo gli eventi e li scrivo nel posto giusto sul display
# tamnto è una sola riga
festa_da_db_domani = ""
for row in righe:
    print("Trovato evento domani")
    festa_da_db_domani = str(row[1])
    
draw.text((75,279), festa_da_db_domani + " " + festa_da_libreria_domani, fill=inkywhat.WHITE, font=font_eventi)    
    
connessione.commit()
connessione.close()



# per leggere consumi e temperature mi collego al DB della centralina di casa
# montando la cartella via SSH e leggendo direttamente dal DB
# questa cosa è fatta nello script di esecuzione del programma, con "sshfs"

# connessione al DB
connessione = sqlite3.connect(db_sqlite_remoto)

# generazione del cursore per le temperature
cursore = connessione.cursor()

# generazione del cursore per i luoghi
cursore_luoghi = connessione.cursor()

# leggo l'elenco dei luoghi
cursore_luoghi.execute("SELECT ID, Descrizione FROM Luoghi;")

# per ogni luogo estraggo le temperature
righe_luoghi = cursore_luoghi.fetchall()

# inizializzo il messaggo
messaggio = "*Report delle temperature:*"


# estraggo i dati dei vari luoghi a partire dai risultati della query precedente
for row_luoghi in righe_luoghi:
    # variabile per verficare se ho trovato o meno dati della stanza
    stanza_con_dati = 0

    # leggo l'ultimo valore memorizzato
    cursore.execute("SELECT ID, strftime('%H:%M', Timestamp, 'localtime'), Luogo, Temp, Umid FROM Temperature WHERE Luogo = " + str(row_luoghi[0]) + " and timestamp > datetime('now','-2 hours') ORDER BY ID DESC LIMIT 1;")
    righe_ultima = cursore.fetchall()
    
    # scrivo le temperature
    for row in righe_ultima:
        messaggio = messaggio + "\n_Alle " + str(row[1]) + " in " + str(row_luoghi[1]) + "_\nT: " + str(row[3]) + " - Umid.: " + str(row[4]) + "%\n"
        stanza_con_dati = 1
        if str(row_luoghi[1]) == "Camera":
            draw.text((215,142), str(row[3])[:4]+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore)
        if str(row_luoghi[1]) == "Sala":
            draw.text((155,103), str(row[3])[:4]+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore)
        if str(row_luoghi[1]) == "Studio":
            draw.text((215,103), str(row[3])[:4]+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore)
        if str(row_luoghi[1]) == "Bagno":
            draw.text((155,142), str(row[3])[:4]+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore)
        if str(row_luoghi[1]) == "Cucina":
            draw.text((155,179), str(row[3])[:4]+"°", fill=inkywhat.BLACK, font=font_temp_ext_valore) 
           
print(messaggio)

# generazione del cursore
cursore = connessione.cursor()

# cerco il consumo di oggi
#cursore.execute("select strftime('%d/%m', the_day), SUM(consumo_medio), strftime('%w', the_day) from ( select the_day, the_hour, AVG(the_count) as consumo_medio from ( select date(timestamp) as the_day, strftime('%H', timestamp) as the_hour, avg(Consumo) as the_count from Corrente group by the_day, the_hour) group by the_day, The_hour) group by the_day order by the_day desc limit 1;")
cursore.execute("SELECT * FROM ConsumoOrario;")
righe = cursore.fetchall()
for row in righe:
    consumoOggi = int(row[1])

print("Consumo oggi: " + str(consumoOggi))

draw.text((275,24), str(consumoOggi)+"Wh", fill=inkywhat.BLACK, font=font_22)

# estraggo i consumi degli ultimi 30 giorni per farne il grafico
cursore.execute("SELECT printf('%.2f',SUM(media)), strftime('%d-%m-%Y', data) FROM (SELECT AVG(consumo) as media, timestamp as data, strftime('%H', timestamp) as ora FROM Corrente GROUP BY DATE(timestamp), strftime('%H',timestamp)) GROUP BY date(data) ORDER BY date(data) DESC LIMIT 29;")
righe = cursore.fetchall()
lettura_consumo = []
altezza_barretta = []
for row in righe:
    print(str(row[1]) + " - " + str(row[0]))
    lettura_consumo.append(float(row[0]))

for potenza in lettura_consumo:
    altezza_barretta.append(altezzaGrafico(potenza, max(lettura_consumo), 5000))

font_limiti_grafico = ImageFont.truetype(font_TTF, 9)
draw.text((360,50), str(truncate(max(lettura_consumo),0))[:-2], fill=inkywhat.BLACK, font=font_limiti_grafico)


print(lettura_consumo)
print(altezza_barretta)

grafico_x = 385
# il punto della base e' 86
for barretta in altezza_barretta:
    draw.line([(grafico_x,86), (grafico_x,86-barretta)], fill=inkywhat.BLACK, width=4)
    grafico_x = grafico_x -4
    
print("Consumo massimo: " + str(max(lettura_consumo)))
print("Consumo minimo: " + str(min(lettura_consumo)))

# estraggo i consumi orari per fare il grafico giornaliero
cursore.execute("SELECT printf('%.2f',AVG(consumo)) as media, timestamp as data, strftime('%H', timestamp) as ora FROM Corrente WHERE strftime('%Y-%m-%d', data) = strftime('%Y-%m-%d', 'now') GROUP BY DATE(timestamp), strftime('%H',timestamp) order by ora LIMIT 24;")
righe = cursore.fetchall()
lettura_consumo_orario = []
altezza_barretta_oraria  = []
print("Consumi per ora")
for row in righe:
    print(str(row[0]) + " - " + str(row[2]))
    lettura_consumo_orario.append(float(row[0]))

for potenza_oraria in lettura_consumo_orario:
    altezza_barretta_oraria.append(altezzaGrafico(potenza_oraria, max(lettura_consumo_orario), 0))

draw.text((360,99), str(truncate(max(lettura_consumo_orario),0))[:-2], fill=inkywhat.BLACK, font=font_limiti_grafico)

grafico_x = 273
# il punto della base e' 126
for barretta in altezza_barretta_oraria:
    draw.line([(grafico_x,126), (grafico_x,126-barretta)], fill=inkywhat.BLACK, width=4)
    grafico_x = grafico_x +5 


# disegno il grafico degli ultimi giorni di letture PM10
cursore.execute("SELECT Valore from PM10 ORDER By ID DESC LIMIT 20;")
righe = cursore.fetchall()
grafico_x = 266
for row in righe:
    # il punto della base è 86
    valore = int(row[0])
    grafico_y = 86-valore/5
    draw.line([(grafico_x,86), (grafico_x,grafico_y)], fill=inkywhat.BLACK, width=3)
    grafico_x = grafico_x -3

# via SNMP cerco di capire quanti dati consumo su Internet
# USO SNMPWALK sui due ISO della porta di WAN Del mikrotik
lettura_dati_up = os.popen("snmpwalk -Os -c public -v 1 " + ip_router + " " + iso_wan_up + " | awk '{print $4}'").read()
lettura_dati_down = os.popen("snmpwalk -Os -c public -v 1 " + ip_router + " " + iso_wan_down + " | awk '{print $4}'").read()
print('Contatore dati Down: ' + str(lettura_dati_down))
print('Contatore dati Up: ' + str(lettura_dati_up))

# se è già stato caricato un valore con questa ora, non ne carico uno doppio
cursore.execute("SELECT * FROM Internet WHERE Data = '" + datetime.now().strftime("%Y-%m-%d") + "' AND Ora = '" + datetime.now().strftime("%H") + "';")
righe = cursore.fetchone()
print(righe)
if righe is None:
    # memorizzo len due letture nel db
    print ("Query insert dati down: " + "INSERT INTO Internet (Data, ora, UpDown, Lettura) VALUES ('" + datetime.now().strftime("%Y-%m-%d") + "', '" + datetime.now().strftime("%H") + "', 'down', " + str(lettura_dati_down) + ");")
    cursore.execute("INSERT INTO Internet (Data, ora, UpDown, Lettura) VALUES ('" + datetime.now().strftime("%Y-%m-%d") + "', '" + datetime.now().strftime("%H") + "', 'down', " + str(lettura_dati_down) + ");")
    print ("Query insert dati down: " + "INSERT INTO Internet (Data, ora, UpDown, Lettura) VALUES ('" + datetime.now().strftime("%Y-%m-%d") + "', '" + datetime.now().strftime("%H") + "', 'up', " + str(lettura_dati_up) + ");")
    cursore.execute("INSERT INTO Internet (Data, ora, UpDown, Lettura) VALUES ('" + datetime.now().strftime("%Y-%m-%d") + "', '" + datetime.now().strftime("%H") + "', 'up', " + str(lettura_dati_up) + ");")

connessione.commit()

# recupero la prima lettura della giornata
cursore.execute("SELECT Lettura, UpDown FROM Internet WHERE Data = '" + datetime.now().strftime("%Y-%m-%d") + "' ORDER BY ORA LIMIT 2;")
righe = cursore.fetchall()
# estraggo gli eventi e li scrivo nel posto giusto sul display
# tamnto è una sola riga
for row in righe:
    if row[1] == "up":
        print("Prima lettura oggi UP: " + str(row[0]))
        prima_up = str(row[0])
    if row[1] == "down":
        print("Prima lettura oggi DOWN: " + str(row[0]))
        prima_down = str(row[0])

#converto i byte in GB        
print("Traffico UP = " + str(truncate((int(lettura_dati_up) - int(prima_up))/1000000000,0))) 
print("Traffico DOWN = " + str(truncate((int(lettura_dati_down) - int(prima_down))/1000000000,0)))
totale_up = str(truncate((int(lettura_dati_up) - int(prima_up))/1000000000,0))[:-2]
totale_down = str(truncate((int(lettura_dati_down) - int(prima_down))/1000000000,0))[:-2]

draw.text((275,142), totale_up + "/" + totale_down, fill=inkywhat.BLACK, font=font_temp_ext_valore)

# qui faccio i grafici dei dati passati dal router
# grafico con le 24 barrette delle 24 ore
# prima l'upload

cursore.execute("SELECT Data, ora, updown, lettura FROM Internet WHERE data = strftime('%Y-%m-%d', 'now') and updown = 'up' order by ora;")
dati_upload = []
righe = cursore.fetchall()
for row in righe:
    dati_upload.append(int(row[3]))
    
print("Dati caricati")    
print(dati_upload)

upload_per_ora = []
for num_ora in range(1, len(dati_upload)-1):
    upload_per_ora.append(round((dati_upload[num_ora] - dati_upload[num_ora -1])/1000000000,0))
    

print("Dati caricati per ora")
print(upload_per_ora)

altezza_barretta_gb_up = []
for gb_up in upload_per_ora:
    altezza_barretta_gb_up.append(altezzaGrafico(gb_up, max(upload_per_ora), 0))

draw.text((370,167), str(truncate(max(upload_per_ora),0))[:-2], fill=inkywhat.BLACK, font=font_limiti_grafico)

grafico_x = 273
# il punto della base e' 205
for barretta in altezza_barretta_gb_up:
    draw.line([(grafico_x,205), (grafico_x,205-barretta)], fill=inkywhat.BLACK, width=4)
    grafico_x = grafico_x +5 

# poi il download
cursore.execute("SELECT Data, ora, updown, lettura FROM Internet WHERE data = strftime('%Y-%m-%d', 'now') and updown = 'down' order by ora;")
dati_download = []
righe = cursore.fetchall()
for row in righe:
    dati_download.append(int(row[3]))
    
print("Dati scaricati")    
print(dati_download)



download_per_ora = []
for num_ora in range(1, len(dati_download)-1):
    download_per_ora.append(round((dati_download[num_ora] - dati_download[num_ora -1])/1000000000,0))
    
draw.text((370,234), str(truncate(max(download_per_ora),0))[:-2], fill=inkywhat.BLACK, font=font_limiti_grafico)

print("Dati scaricati per ora")
print(download_per_ora)


altezza_barretta_gb_dn = []
for gb_dn in download_per_ora:
    altezza_barretta_gb_dn.append(altezzaGrafico(gb_dn, max(download_per_ora), 0))

grafico_x = 272
# il punto della base e' 205
for barretta in altezza_barretta_gb_dn:
    draw.line([(grafico_x,205), (grafico_x,205+barretta)], fill=inkywhat.BLACK, width=4)
    grafico_x = grafico_x +5 
    
connessione.close()

# recuperiamo il meteo di Torino
url =  "http://api.openweathermap.org/data/2.5/forecast?id=" + owm_id_city + "&appid=" + owm_api + "&units=metric"
response = requests.request("GET", url)
dati_meteo = response.json()
previsioni = dati_meteo['list']


# le API restiuiscono le previsioni ogni 3 ore dei prossimi 5 giorni
# visto che ho solo due caselle, uso la previsione di oggi, che alla fine è lo stato attuale del tempo
# che potrei guardare dalla finestra, e poi prendo la previsione di domani.
# l'icona la decido in base alla previsione delle ore 12, mentre temperatura massima e minima la prendo
# dalle previsioni ogni 3 ore, la minima delle minime e la massima delle massime

# le icone sono nel filesyste e non fanno differenza tra giorno e nott,e ma sono numerate come sul sito,
# per questo motivo prendo il nome del file e tolgo l'ultimo carattere che identifica se è giorno o notte.
id_previsione = 1
meteo_temp_max_domani_serie = []
meteo_temp_min_domani_serie = []
for righe in previsioni:
    if id_previsione == 1:
        print(righe['dt_txt'])
        print(righe['weather'][0]['description'])
        meteo_txt_oggi = righe['weather'][0]['description']
        print(righe['main']['temp_min'])
        meteo_temp_max_oggi = righe['main']['temp_max']
        meteo_temp_min_oggi = righe['main']['temp_min']
        print(righe['main']['temp_max'])
        print(righe['weather'][0]['icon'])
        meteo_icona_oggi = "/home/pi/what/icone_meteo/" + righe['weather'][0]['icon'][:-1] + ".png"
    else:
        domani = dt.datetime.now() + dt.timedelta(days=1)
        domani_formattata = domani.strftime('%Y-%m-%d') 
        domani_lunga = domani.strftime('%Y-%m-%d') + " 12:00:00"
        if righe['dt_txt'][:-9]== domani_formattata:
            print("Domani per previsioni: " + domani_formattata)
            print(righe['dt_txt'])
            print(righe['weather'][0]['description'])
            print(righe['weather'][0]['icon'])
            print(righe['main']['temp_min'])
            print(righe['main']['temp_max'])
            meteo_temp_max_domani_serie.append(righe['main']['temp_max'])
            meteo_temp_min_domani_serie.append(righe['main']['temp_min'])
            if righe['dt_txt']== domani_lunga:
                meteo_icona_domani = "/home/pi/what/icone_meteo/" + righe['weather'][0]['icon'][:-1] + ".png"
    id_previsione = id_previsione + 1
    
#disegni e temperature del meteo
#oggi
meteo_logo = Image.open(meteo_icona_oggi)
img.paste(meteo_logo, (12,212))
draw.text((51,212), str(meteo_temp_max_oggi)[:-3] + "°", fill=inkywhat.BLACK, font=font_12)
draw.text((51,230), str(meteo_temp_min_oggi)[:-3] + "°", fill=inkywhat.BLACK, font=font_12)

#domani
meteo_logo = Image.open(meteo_icona_domani)
img.paste(meteo_logo, (77,212))
#draw.rectangle([(77,212), (114, 242)], outline=inkywhat.BLACK, width=1)
draw.text((117,212), str(truncate(max(meteo_temp_max_domani_serie),0))[:-2] + "°", fill=inkywhat.BLACK, font=font_12)
draw.text((117,230), str(truncate(min(meteo_temp_min_domani_serie),0))[:-2] + "°", fill=inkywhat.BLACK, font=font_12)


# per debug, l'ora dell'aggiornamento
font_ora = ImageFont.truetype(font_TTF, 12)
print("Ora di update: " + dt.datetime.fromtimestamp(time.time()).strftime('%H:%M'))
draw.text((150,245), "Agg: " + dt.datetime.fromtimestamp(time.time()).strftime('%H:%M'), fill=inkywhat.BLACK, font=font_ora)

# per debug, IP delle interfacce di rete
indirizzo_eth0 = os.popen("/sbin/ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'").read()
indirizzo_eth0 = indirizzo_eth0.replace('\n', '')
indirizzo_wlan0 = os.popen("/sbin/ifconfig wlan0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'").read()
indirizzo_wlan0 = indirizzo_wlan0.replace('\n', '')
draw.text((220,245), indirizzo_eth0 + " " + indirizzo_wlan0, fill=inkywhat.BLACK, font=font_ora)


# si invia il buffer al display
inkywhat.set_image(img)
inkywhat.show()
