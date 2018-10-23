/*
 * Questo sketch fa parete del progetto www.ladomoticafaidame.it
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
 * Versione 1.0 del 23/10/2018
 * 
 * Puoi usare questo progetto a sé stante comandandolo via http
 * oppure puoi integrarlo nel progetto più grande della Domotica fai-da-me.
 * In ultimo, puoi implementarlo in un altro tuo progetto, adattando il codice
 */

#include <Adafruit_NeoPixel.h> // libreria per comandare il LED RGB - https://github.com/adafruit/Adafruit_NeoPixel
#include <ESP8266WiFi.h>  // libreria per usare la comunicazione WiFi - https://github.com/esp8266/Arduino/tree/master/libraries/ESP8266WiFi
#define PIN D2

// creo un nuovo oggetto per il LED RGB
Adafruit_NeoPixel pixels = Adafruit_NeoPixel(1, PIN, NEO_GRB + NEO_KHZ800);

// parametri della rete WiFi
const char* ssid     = "SSID WiFi"; 
const char* password = "Password WiFi";

int ledPin = D5; // PIN al quale è collegato il LED sulla shield WeMos
WiFiServer server(80); // crea un web server sulla porta 80 (la standard per le chiamate http)


// questa funzione viene eseguita una sola volta all'avvio della scheda
void setup() {
  pixels.begin(); // Inizializza la libreria per il LED RGB
  Serial.begin(115200); // Attivo il debug sulla porta seriale
                        // tutti i serial.print messi dopo sono tutti per debug.
                        // volendo si pososno togliere una volta che la scheda funziona correttamente
  delay(10); // pausa di 10 millisecondi
 
  // Mi collego alla rete WiFi
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  // aspetto che la WiFi si connetta, ogni mezzo secondo scrivo un puntino sulla seriale
  // se la WiFI non si connette il sistema non esce da questo ciclo
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // la WiFi qui si è connessa.
  Serial.println("");
  Serial.println("WiFi connected");
 
  // Avvio il server web
  server.begin();
  Serial.println("Server started");
 
  // Per debug, scrivo sulla seriale il link da usare, copmpreso indirizzo IP
  Serial.print("Per comandare, usa questa URL : ");
  Serial.print("http://");
  Serial.print(WiFi.localIP());
  Serial.println("/");

  // WiFi connessa, server attivo, adesso accendo il LED di colore bianco non troppo forte
  pixels.setPixelColor(0, pixels.Color(32, 32, 32));  
  pixels.show(); // Abilito la visualizzazione impostata sulla riga di prima  



}

// questa procedura viene eseguita a ciclo per sempre
void loop() {

  // Controlla se un client si è collegato al server web
  WiFiClient client = server.available();
  if (!client) {
    return;
  }
 
  // Il client si è collegato, aspetto che invvi dati
  Serial.println("new client");
  while(!client.available()){
    delay(1);
  }
 
  // Leggo la prima riga dell comandoi inviato via http
  String request = client.readStringUntil('\r');
  Serial.println(request);
  client.flush();
 
  // Adesso elaboro la richiesta

   // imposto le varibili che uso per il LED
  int value = LOW;
  int rosso;
  int verde;
  int blu;

  // ignoro la richiesta della favicon fatta dal browser
  if (request != "GET /favicon.ico HTTP/1.1"){

    // ewstraggo i tre valori per R, G e B (3 caratteri per ogni colore)
    // la chiamata http deve essere http://[indirizzo ip]/RRRGGGBBB con RRR, GGG e BBB da 000 a 255
    rosso = request.substring(5,8).toInt();
    verde = request.substring(8,11).toInt();
    blu = request.substring(11,14).toInt();
    Serial.println(rosso);
    Serial.println(verde);
    Serial.println(blu);
    pixels.setPixelColor(0, pixels.Color(rosso, verde, blu)); // imposto il colore estratto dalla stringa  
    pixels.show(); // Attivo la visuializzazione del colore 
  }  

 
 
 
  // Return the response
  client.println("HTTP/1.1 200 OK");

  delay(1);
  Serial.println("Client disconnected");
  Serial.println("");
}
