#include <OneWire.h>
#include <DallasTemperature.h>
#include <PZEM004Tv30.h>
#include <SoftwareSerial.h>
#include <avr/wdt.h>  // Biblioteca para o Watchdog Timer

#define ONE_WIRE_BUS 3
#define PZEM_RX_PIN 12
#define PZEM_TX_PIN 13
#define SAMPLE_INTERVAL 500  // Intervalo de amostragem em milissegundos (500 ms)
#define SENSOR_PORTA 9       // Pino PB1 (Pino 9 no ATmega328)

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

SoftwareSerial pzemSWSerial(PZEM_RX_PIN, PZEM_TX_PIN);
PZEM004Tv30 pzem(pzemSWSerial);

unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(9600);
  sensors.begin();             // Inicia o sensor de temperatura
  pinMode(SENSOR_PORTA, INPUT); // Configura o pino do sensor de porta como entrada

  // Configurar o Watchdog Timer para 8 segundos (o maior intervalo disponível diretamente)
  wdt_enable(WDTO_8S);
}

void loop() {
  // Reinicia o Watchdog Timer para evitar o reset
  wdt_reset();

  // Verifica se o intervalo de amostragem foi atingido
  if (millis() - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = millis();

    // Solicita e lê a temperatura
    sensors.requestTemperatures();
    float currentTemp = sensors.getTempCByIndex(0);
    float currentTemp2 = sensors.getTempCByIndex(1);

    // Exibe a temperatura atual na Serial
    Serial.print("Temperatura: ");
    Serial.print(currentTemp);
    Serial.println(" *C");

    Serial.print("Temperatura2: ");
    Serial.print(currentTemp2);
    Serial.println(" *C");
  }

  // Leitura dos dados do PZEM
  float voltage = pzem.voltage();
  float current = pzem.current() -0.04;
  //float power = pzem.power() - 0.40;
  float power = voltage*current;
  float frequency = pzem.frequency();
  float pf = pzem.pf() - 0.05;

  // Tratamento de NaN para os valores do PZEM
  if (isnan(voltage)) {
    Serial.println("Error reading voltage, setting to 0");
    voltage = 0.0;
    current = 0.0;
    power = 0.0;
    frequency = 0.0;
    pf = 0.0;
  }
  if (isnan(current)) {
    Serial.println("Error reading current");
    current = 0.0;
  }
  if (isnan(power)) {
    Serial.println("Error reading power");
    power = 0.0;
  }
  if (isnan(frequency)) {
    Serial.println("Error reading frequency");
    frequency = 0.0;
  }
  if (isnan(pf)) {
    Serial.println("Error reading power factor");
    pf = 0.0;
  }

  // Exibir valores do PZEM no console Serial
  Serial.print("Voltage: ");
  Serial.print(voltage);
  Serial.println(" V");

  Serial.print("Current: ");
  Serial.print(abs(current));
  Serial.println(" A");

  Serial.print("Power: ");
  Serial.print(abs(power));
  Serial.println(" W");

  Serial.print("Frequency: ");
  Serial.print(frequency, 1);
  Serial.println(" Hz");

  Serial.print("PF: ");
  Serial.println(abs(pf));

  // Ler e exibir o valor do sensor de porta diretamente
  int estadoPorta = digitalRead(SENSOR_PORTA);
  Serial.print("SensorPorta: ");
  Serial.println(estadoPorta); // 1 significa porta aberta, 0 significa porta fechada

  Serial.println();  // Linha em branco para separar leituras

  // Delay para manter o ciclo dentro do limite do Watchdog Timer
  delay(2000);  // Aguarda 2 segundos antes da próxima leitura
}
