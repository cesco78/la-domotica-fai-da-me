/*
 * Questo sketch fa parte del progetto www.ladomoticafaidame.it
 * Tutte le informazioni relative al progetto o allo schema dei 
 * componenti può essere trovato sul sito.
 * 
 * Il progetto è distribuito con licenza GPL v.3
 * Puoi usare liberamente questo codice, puoi modificarlo
 * a seconda delle tue necessità e puoi distribuirlo.
 * Devi mantenere la citazione dello sviluppatore e 
 * devi distribuirlo con la stessa licenza.
 * 
 * Il progetto è di Francesco Tucci
 *  www.iltucci.com
 *  twitter.com/cesco_78
 *  
 * Versione 1.0 del 17/10/2018
 * 
 * Puoi usare questo progetto senza tutta la parte di rete, 
 * solo con la visualizzazione del consumo in tempo reale, 
 * per farlo funzionare correttamente devi rimuovere tutti i riferimenti
 * alla connessione WiFi e MQTT
 */



// Include la libreria per la lettura della pinza amoerometrica
// Questa libreria si può trovare qui: https://github.com/openenergymonitor/EmonLib
// oppure si può installare direttamente dentro l'IDE di Arduino
#include "EmonLib.h"

// Queste librerie sono utilizzate per la gestione del display OLED
#include <SPI.h> // https://www.arduino.cc/en/Reference/SPI 
#include <Wire.h> // https://www.arduino.cc/en/Reference/Wire
#include <Adafruit_GFX.h> // https://github.com/adafruit/Adafruit-GFX-Library
#include <Adafruit_SSD1306.h> // https://github.com/stblassitude/Adafruit_SSD1306_Wemos_OLED

#include <ESP8266WiFi.h> // libreria per usare la comunicazione WiFi - https://github.com/esp8266/Arduino/tree/master/libraries/ESP8266WiFi
#include <PubSubClient.h> // libreria per la comunicazione MQTT - https://pubsubclient.knolleary.net/


// parametri di calibrazione per la pinza amperometrica
const int volt = 220;
const float ct_calibration = 29;

// Pin analogico per la lttura del valore dalla pinza amperometrica
const int currentSensorPin = A0;

// variabili necessarie per il sistema
float tempValue = 0;
float Irms = 0;
float lettura;
int lightValue = 0;
char suSchermo[8];
char messaggio[12];
String stringaGet;
int cicliGet = 0;
long sommaPerMedia = 0;

// Oggetto per la lettura della corrente
EnergyMonitor emon1; 

// inizializzazione del display OLED
// SCL GPIO5
// SDA GPIO4
#define OLED_RESET 0  // GPIO0
Adafruit_SSD1306 display(OLED_RESET);

// Parametri necessari per usare il display OLED
#define NUMFLAKES 10
#define XPOS 0
#define YPOS 1
#define DELTAY 2
#define LOGO16_GLCD_HEIGHT 16
#define LOGO16_GLCD_WIDTH  16

// dati della WiFi
const char* ssid     = "WIFI SSID"; 
const char* password = "WIFI Password";

// inizializzazione comunicazione MQTT
WiFiClient espClient;
PubSubClient client(espClient);

const char* mqtt_server ="IP MQTT Broker"; //per trasmettere i dati via MQTT ci deve essere l'indirizzo IP del broker
char temp[8]; // la trasmissione dei dati su MQTT va fatta in array di caratteri
int tempoTrasmissione = 0; // la lettura sul display è istantanea, ma la trasmissione al server va fatta molto più raramente
int tentativiConnessione = 0; // dopo un certo numero di tentativi abortisce la connessione MQT
int mqttConnection = 0; //stato dell'ultima connessione a MQTT
char watt[8];
char wattTrasmettere[8];

// funzione per la connessione MQTT
void reconnect() {
  // Esegue questo ciclo fino a quando non riesce a connettersi
  while (!client.connected()) {
    tentativiConnessione == 10; //fa 10 tentativi
    Serial.print("Provo la connessione MQTT");
    // Questo è il nome del dispositivo che verrà visto dal broker MQTT
    String clientId = "ESP8266Client-Corrente";
    // Effettuo la connessione
    if (client.connect(clientId.c_str())) {
      Serial.println("Connesso!");
      mqttConnection = 1;     
    } else {
      Serial.print("Connessione fallita, rc=");
      Serial.print(client.state());
      Serial.println(" -> riprovo tra 5 secondi");
      // Aspetta 5000 millisecondi prima di rifare le connessione (5 secondi)
      delay(5000);
      tentativiConnessione = tentativiConnessione +1;
      // se ho provato la connessione 10 volte ed è fallita, allora ci rinuncio
      if (tentativiConnessione == 10) {
        mqttConnection = 0;
        break;
      }
    }
  }
}

// inizializzazione sistema
// questa funzione viene eseguita solo all'accensione della scheda
void setup() {
  // avvia la porta seriale (per debug)
  Serial.begin(9600);

  // creo il client MQTT per la connesisone al server
  client.setServer(mqtt_server, 1883);
  Serial.println("Crea MQTT client");

  // inizializza il lettore di corrente
  emon1.current(currentSensorPin, ct_calibration);
  Serial.println("Inizializza sensore corrente");

  // Inizializzo il display OLED
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // sulla seriale I2C con indirizzo 0x3C
  display.display();
  delay(1);
  display.clearDisplay();
  Serial.println("Inizializza display");

  // inizializzare la WiFi
  Serial.println("partiamo con la WiFi");
  WiFi.begin(ssid, password); // dati della wifi

  // impostro il carattere e il cursore sul display
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  
  display.print("WiFi");  // scrivo WiFi sul display
  display.display();

  // ripeto fino a quando la WiFi non è connessa
  // attenzione, se la connessione WiFi non c'è il sistema non
  // uscirà mai da questo ciclo 
  // (se non si usa la WiFi questa roba non serve, ovviamente)
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); //aspetto mezzo secondo
    display.print("."); // scrivo un puntino
    display.display();
    Serial.print(".");
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
  
  }

  // se sono qui la connessione WiFi è avvenuta con successo
  // quindi scrivo l'indirizzo IP ottenuto dal DHCP server
  display.setCursor(0,0);
  display.print(WiFi.localIP()); 
  Serial.println(WiFi.localIP());
  display.display();
  delay(2000); // pausa di due secondi
}

// questa invece è la funzione che viene eseguita per sempre, 
// fino a quando la scheda non sarà spenmta
void loop() {

  // fa 10 letture consecutive ogni 0,1 secondi e poi ne fa la media
  // faccio questo eprché a volte la lettura genera dei picchi fuori contesto,
  // con la media du 10 letture i picchi sono quasi annullati
  // o almeno influiscono meno
  lettura = 0;
  for (int c = 0; c<10; c++)
    { 
      lettura = lettura + (emon1.calcIrms(1480));
      delay(100);
    }
  Irms = lettura / 10;
  
  // debug, visualizza vie seriale i dati letti
  Serial.print("W : ");
  Serial.println(Irms*volt);

  // visualizza la lettura sul display    
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  dtostrf(Irms*volt, 4, 0, watt);
  display.print(watt);
  display.println("W");
  display.setTextSize(1);
  display.println("");
  display.println("Consumo");
  display.println("istantaneo");
  display.display();

  // la lettura viene inviata al server MQTT ogni 50 cicli di 10 letture
  // quindi circa ogni 50 secondi
  // viene inviata la media di tutte le letture
  sommaPerMedia = sommaPerMedia + int(Irms*volt);  
    // se ho fatto 50 aggiornamenti è ora di scrivere il dato sul DB
    if (cicliGet == 50)
    { 
      Serial.println("get: " + cicliGet);
    
      // se non sono più connesso al server MQTT rifaccio la connessione
      // (il server MQTT dopo un po' che non riceve dati va in timeout
      if (!client.connected()) {
        Serial.println("mi devo riconnettere");
        reconnect();
      }
       
      dtostrf(sommaPerMedia/50, 8, 0, wattTrasmettere); //converto il valore da trasmettere in stringa 
      Serial.print("Trasmetto ");
      Serial.println(wattTrasmettere);
      client.publish("topicCorrente", wattTrasmettere); // effettiva trasmissione via MQTT

      // azzero il contatore dei clici e la media
      // così posso ricominciare
      cicliGet = 0;
      sommaPerMedia = 0;
    }
    // se non è ancora il tempo di trasmettere aumento i cicli di uno
    else
    {
      cicliGet = cicliGet + 1;
    }
}
