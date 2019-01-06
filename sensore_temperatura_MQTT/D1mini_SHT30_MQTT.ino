/*
 * Questo sensore di temperatura fa parte del progetto www.ladomoticafaidame.it
 * usa un sensore SHT ed è alimentato a batteria
 * 
 * Dispositivi necessari:
 * - WeMos D1 mini
 * - shield sensore temperatura SHT30
 * - opzionale: shield per batteria LiPo.
 * 
 * Librerie utilizzate:
 * - SHT30 https://github.com/wemos/WEMOS_SHT3x_Arduino_Library
 * - PubSubCLient per MQTT  https://github.com/plapointe6/EspMQTTClient
 * 
 * Il codice è liberamente utilizzabile, modificabile e condivisibile secondo la licenza GPL v3.0
 * E' necessario lasciare questa introduzione all'inizio.
 * 
 * Versione 1.0 del 06/01/2019
 */


#include <WEMOS_SHT3X.h> // libreria per leggere i dati dal sensore
#include <ESP8266WiFi.h> // libreria per il WiFi dell'ESP
#include <PubSubClient.h> // libreria per la comunicazine MQTT

// dati della WiFi
const char* ssid     = "..."; 
const char* password = "...";

// inizializzazione comunicazione MQTT
WiFiClient espClient;
PubSubClient client(espClient);
const char* mqtt_server ="192.168.1.1"; // l'IP del server con il Broker MQTT attivo

/*
 * Qui creiamo l'oggetto del sensore indicando l'indirizzo sul quale 
 * lo troviamo sul bus seriale I2C
 */
SHT3X sht30(0x45);

// definizione di variabili che ci serviranno durante l'elaborazione del codice
float leggiTemp;
float letturaTemp, letturaHumid;
float tensioneBatteria;

// la trasmissione dei dati su MQTT va fatta in array di caratteri
char temp[8];
char humid[8];
char batt[8];
char stringaPayload[64];

// variabili per la lettura della batteria
unsigned int raw=0;
float volt=0.0;

void reconnect() {
  // Questo ciclo non termina fino a quando 
  // la connessione MQTT non avviene
  while (!client.connected()) {
    Serial.print("Connessione MQTT in corso...");

    // il client ID deve essere univoco nella rete MQTT
    String clientId = "ESP8266Client-PIPPO";
    
    // Avvia la connessione
    if (client.connect(clientId.c_str())) {
      Serial.println("Connesso!");
    } else {
      Serial.print("Non connesso, errore=");
      Serial.print(client.state());
      Serial.println(" aspetto 5 secondi");
      // se qualcosa non va apetta 5 secondi
      delay(5000);
    }
  }
}


/*
 * Il "setup" è una parte di codice che viene eseguita solo all'avvio della scheda, poi mai più
 */
void setup()   
{
  /* 
   * inizializzare la comunicazione seriale è sempre utile per debug,  
   * Aprendo il monitor seriale potremmo vedere tutto quello che ci serve per identificare eventuali problemi
   */
  Serial.begin(9600);

  // connessione alla WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { // fino a che il WiFi non è connesso
    delay(500);
    Serial.print("."); // disegno un puntino ogni mezzo secondo
    }
  Serial.println(WiFi.localIP()); // una volta connesso scrivo l'IP ottenuto sulla seriale

  // questo mi serve per leggere la tensione della batteria
  pinMode(A0, INPUT); 
  
  
  // creo il client MQTT per la connesisone al server
  client.setServer(mqtt_server, 1883);

}

/*
 * Il "loop" è una funzione che viene eseguita a ciclo per tutta la
 * durata in vita accesa della scheda.
 */
void loop() {

  sht30.get(); //legge i dati del sensore
  letturaTemp = sht30.cTemp; // memorizza la temperatura in Celsius
  letturaHumid = sht30.humidity; // memorizza l'umidità

  // legge la tensione della batteria
  raw = analogRead(A0);
  volt=raw/1023.0;
  volt=volt*4.2;

  // debug: su seriale la temperatura e l'umidità appena letti
  Serial.print("Temperatura: ");
  Serial.println(sht30.cTemp);
  Serial.print("Umidità: ");
  Serial.println(sht30.humidity);  
  Serial.print("Batteria: ");
  Serial.println(raw);    

  if (!client.connected()) {
    Serial.println("mi devo riconnettere");
    reconnect();
  }
  // converto la temperatura in stringa 
  dtostrf(letturaTemp, 4, 2, temp); 

  // converto l'umidità in stringa
  dtostrf(letturaHumid, 4, 2, humid);

  // converto la tensione in stringa
  dtostrf(volt, 2, 2, batt);

  // creo la stringa da inviare
  sprintf(stringaPayload, "%s # %s # %s", temp, humid, batt);
  
  Serial.print("Trasmetto ");
  Serial.println (stringaPayload);
  client.publish("topicBagno", stringaPayload);

  delay(4000);
  Serial.print("sleep mode");
  ESP.deepSleep(1800000000);  // lo sleep è in microsecondi 1.800.000.000 = mezz'ora)
}
