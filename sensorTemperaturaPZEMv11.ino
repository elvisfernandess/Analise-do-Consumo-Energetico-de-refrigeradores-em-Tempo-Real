#include <OneWire.h> //biblioteca para os sensores de temperatura
#include <DallasTemperature.h> //biblioteca para os sensores de temperatura
#include <PZEM004Tv30.h> //biblioteca para o sensor de energia
#include <SoftwareSerial.h> //biblioteca para criar portas seriais
#include <avr/wdt.h>  //biblioteca para o Watchdog Timer

#define ONE_WIRE_BUS 3 //pino dos sensores de energia
#define PZEM_RX_PIN 12 //pino rx do sensor de energia
#define PZEM_TX_PIN 13 //pino tx do sensor de energia
#define SAMPLE_INTERVAL 500  //intervalo de amostragem em milissegundos (500 ms)
#define SENSOR_PORTA 9       //pino do sensor de porta PB1 (Pino 9 no ATmega328)

OneWire oneWire(ONE_WIRE_BUS); //objeto para a comunicação do sensor de temperatura
DallasTemperature sensors(&oneWire); //objeto para o barramento do sensor de temperatura

SoftwareSerial pzemSWSerial(PZEM_RX_PIN, PZEM_TX_PIN); //cria uma porta virtual para comunicação passando os pinos do sensor de energia como parâmetro
PZEM004Tv30 pzem(pzemSWSerial); //inicia  a comunicação usando a porta virtual

unsigned long lastSampleTime = 0; //armazena o ultimo tempo de amostragem

void setup() {
  Serial.begin(9600);		    //baud rate da porta serial
  sensors.begin();             //inicia o sensor de temperatura
  pinMode(SENSOR_PORTA, INPUT); //configura o pino do sensor de porta como entrada
  wdt_enable(WDTO_8S); //configurar o Watchdog Timer para 8 segundos (o maior intervalo disponível diretamente)
}

void loop() {
  wdt_reset(); //reinicia o Watchdog Timer para evitar o reset

  if (millis() - lastSampleTime >= SAMPLE_INTERVAL) {  //verifica se o intervalo de amostragem foi atingido
    lastSampleTime = millis(); //atualiza o tempo da última amostragem

    sensors.requestTemperatures(); //requisição para todos os sensores de temperatura que estão nesse barramento
    float currentTemp = sensors.getTempCByIndex(0); //pega a temperatura do sensor de temperatura 1
    float currentTemp2 = sensors.getTempCByIndex(1); //pega a temperatura do sensor de temperatura 1

    Serial.print("Temperatura: ");  //exibe a temperatura do sensor 1 atual na serial
    Serial.print(currentTemp);
    Serial.println(" *C");

    Serial.print("Temperatura2: "); //exibe a temperatura do sensor 1 atual na serial
    Serial.print(currentTemp2);
    Serial.println(" *C");
  }

  float voltage = pzem.voltage(); //pega a tensão medida do sensor de energia
  float current = pzem.current() -0.04; //pega a corrente medida do sensor de energia e calibra
  //float power = pzem.power() - 0.40;
  float power = voltage*current; //calcula a potencia ativa do sensor de energia
  float frequency = pzem.frequency(); //pega a frequencia medida do sensor de energia
  float pf = pzem.pf() - 0.05; //pega o fator de potencia do sensor de energia e calibra

  //se a carga conectada ao sensor de energia estiver desernegizada a serial exibe Nan e isso atrapalha no processamento de dados 
  if (isnan(voltage)) {  //tratamento de NaN para os valores de tensão do sensor de energia
    Serial.println("Error reading voltage, setting to 0");
    voltage = 0.0; //inicializa tensão com zero
    current = 0.0; //inicializa corrente com zero
    power = 0.0; //inicializa potencia ativa com zero
    frequency = 0.0; //inicializa frequencia com zero
    pf = 0.0; //inicializa fator de potencia com zero
  }
  if (isnan(current)) { //tratamento de NaN para os valores de corrente do sensor de energia
    Serial.println("Error reading current");
    current = 0.0;
  }
  if (isnan(power)) { //tratamento de NaN para os valores de potencia ativa do sensor de energia
    Serial.println("Error reading power");
    power = 0.0;
  }
  if (isnan(frequency)) { //tratamento de NaN para os valores de frequencia do sensor de energia
    Serial.println("Error reading frequency");
    frequency = 0.0;
  }
  if (isnan(pf)) { //tratamento de NaN para os valores do fator de potencia do sensor de energia
    Serial.println("Error reading power factor");
    pf = 0.0;
  }

  Serial.print("Voltage: "); //exibe valores lidos de tensão no console Serial
  Serial.print(voltage);
  Serial.println(" V");
	
  Serial.print("Current: "); //exibe valores lidos de corrente no console Serial
  Serial.print(abs(current));
  Serial.println(" A");

  Serial.print("Power: "); //exibe valores lidos de potencia ativa no console Serial
  Serial.print(abs(power)); //apenas valores positivos
  Serial.println(" W");

  Serial.print("Frequency: "); //exibe valores lidos de frequencia no console Serial
  Serial.print(frequency, 1); //com uma casa decimal
  Serial.println(" Hz");

  Serial.print("PF: "); //exibe valores lidos do fator de potencia no console Serial
  Serial.println(abs(pf)); //apenas valores positivos

  int estadoPorta = digitalRead(SENSOR_PORTA);  //lê o valor do sensor de porta diretamente
  Serial.print("SensorPorta: ");  //exibe o valor do sensor de porta
  Serial.println(estadoPorta); //1 significa porta aberta, 0 significa porta fechada

  Serial.println();  //linha em branco para separar leituras

  delay(2000);  //delay para manter o ciclo dentro do limite do Watchdog Timer
}
