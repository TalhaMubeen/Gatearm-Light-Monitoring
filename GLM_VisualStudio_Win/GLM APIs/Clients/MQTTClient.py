import paho.mqtt.client as mqtt
import Client.MQTTClientConfigurations as configs
from   Diagnostics import LocalLogger
import json


class MQTTClient(object):

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self):
        self.__configurations__ = configs
        self.__logger__         = LocalLogger("GLM_Diagnostics", self.whoami())
        self.__mqttClient__     = mqtt.Client()
        self.__mqttClient__.on_connect      = self.__On_Connect__
        self.__mqttClient__.on_subscribe    = self.__On_Subscribe__
        self.__mqttClient__.on_message      = self.__On_Message__
        self.__msg_rcv_callback__           = {}
         
    def RegisterMessageRecieveCallback(self, topic, function):
        """
        register on_mqtt_msg_rcvd callback for multiple functions
        """
        if type(topic) is str :
            if self.__msg_rcv_callback__.get(topic) == None:
                self.__msg_rcv_callback__[topic] = function
            else:
                self.__logger__.log(self.__logger__.ERROR, 'callback to topic ' + topic + ' is already registered')
        else:
            self.__logger__.log(self.__logger__.ERROR, 'topic type must be string to register callback function')

    def IsConnected(self):
        """
        returns boolean if mqtt client is connected or not
        """
        return self.__mqttClient__.is_connected
    
    def __Get_Subscription_Topic__(self, topic):
        """takes the topic name as returns a complete mqtt subscription topic i.e: customer/product/topic """
        return self.__configurations__.Customer + "/" + self.__configurations__.Product + "/" + topic 

    #subscribes to mqtt topic
    def __Subscribe__(self, topic):
        topic = self.__Get_Subscription_Topic__(topic)
        self.__mqttClient__.subscribe(topic, self.__configurations__.QOS)
        topic = "TekTracking/GLM/test/command"
        self.__mqttClient__.subscribe(topic, self.__configurations__.QOS)
    
    def __On_Subscribe__(self,client, userdata, mid, granted_qos):
        """called by mqttclient on subscription to any topic must be called after calling mqtt connect connect """
        self.__logger__.log(self.__logger__.DEBUG, "Subscribed Topics Count: " + str(mid) + " with QOS :" + str(granted_qos))

    #Mqtt On message recieved Callback
    def __On_Message__(self,client, obj, msg):
        str_data = str(msg.payload.decode("utf-8"))
        self.__logger__.log(self.__logger__.DEBUG, msg.topic + " " + str_data)
       
        #retrive the last element from complete topic string 
        topic_str = msg.topic.split('/')[-1]
        
        #if a callback is registered on this topic 
        if self.__msg_rcv_callback__.get(topic_str) != None:
            self.__msg_rcv_callback__[topic_str](str_data)

    def __Connect__(self):
        """
        Use this function to Connect the mqtt client
        """
        host        = self.__configurations__.HOST_ADDRESS
        port        = self.__configurations__.PORT
        keepAlive   = self.__configurations__.KEEP_ALIVE_INTERVAL;
        self.__mqttClient__.connect(host = host, port = port , keepalive = keepAlive)
    
    def __On_Connect__(self, client, userdata, flags, rc):
        """
        possible mqtt return codes 
        0: Connection successful
        1: Connection refused - incorrect protocol version
        2: Connection refused - invalid client identifier
        3: Connection refused - server unavailable
        4: Connection refused - bad username or password
        5: Connection refused - not authorised
        """
        
        if rc == 0: #connection is successful
            self.__logger__.log(self.__logger__.DEBUG,'MQTT Client Connected Successfully')
            self.__Subscribe__(self.__configurations__.TOPIC)
        else :
            self.__logger__.log(self.__logger__.ERROR, 'Failed to Connect MQTT Client, Reason : ' + str(rc))

    def Start(self):
        """
        Start mqtt client to connect and subscribe
        """
        self.__Connect__();
        self.__mqttClient__.loop_start()
