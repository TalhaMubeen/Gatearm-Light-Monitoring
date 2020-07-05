import paho.mqtt.client as mqtt
from   Diagnostics import LocalLogger
import json


class MQTTClient(object):

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs = {}):
        try:
            self.__logger__     = LocalLogger("GLM_Diagnostics", self.whoami(), configs)
            self.__configs__    = configs["GLM"]["MQTT"]
            self.MY_ID          = configs['GLM']['MY_ID']
            self.__mqttClient__     = mqtt.Client(client_id=self.MY_ID, clean_session=False)
            self.currentSubTopic    = ''
            self.currentTopicCount  = 0
            username = self.__configs__["USER_NAME"]
            password = self.__configs__["PASSWORD"]

            self.__mqttClient__.username_pw_set(username=username, password=password)

            self.__mqttClient__.on_connect      = self.__On_Connect__
            self.__mqttClient__.on_subscribe    = self.__On_Subscribe__
            self.__mqttClient__.on_message      = self.__On_Message__
            self.__mqttClient__.on_disconnect   = self.__On_Disconnect__
            self.__msg_rcv_callback__           = {}
            self.__default_status_topic__       = ''
            self.__subscription_map__           = {}
            self.__MessageQueue__               = {}
            self.isReconnected = False
        except:
            self.__logger__.log(self.__logger__.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()

    def __On_Disconnect__(self, client, userdata, rc):
        self.isReconnected = True
        self.__mqttClient__.reconnect()
        if rc != 0:
            print("Unexpected disconnection.")
            #self.__mqttClient__.reconnect()

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

    def __Get_Subscription_Topic__(self, product = None, topic = None):
        """ returns a complete mqtt subscription topic i.e: customer/product/topic """
        if product == None:
            product = self.__configs__["Product"]
 
        return self.__configs__["Customer"] + "/" + product + "/" + topic 

    def MakeSubscriptionMap(self):
        topic = self.__Get_Subscription_Topic__(product='SLM', topic=self.__configs__['TOPIC'])
        self.__subscription_map__[0] = topic

        topic = self.__Get_Subscription_Topic__(topic =self.MY_ID) +"/command"
        self.__subscription_map__[1] = topic

        topicsplit = topic.split('/')
        topicsplit[-1] = 'status'
        topic = "/".join(topicsplit)
        self.__default_status_topic__  = topic

    #subscribes to mqtt topic
    def __Subscribe__(self):
        if len(self.__subscription_map__):
            self.currentSubTopic = self.__subscription_map__[self.currentTopicCount]
            self.__mqttClient__.subscribe(self.currentSubTopic, self.__configs__["QOS"])
            del(self.__subscription_map__[self.currentTopicCount])
        else:
            pass
    
    def __On_Subscribe__(self,client, userdata, mid, granted_qos):
        """called by mqttclient on subscription to any topic must be called after calling mqtt connect connect """
        self.__logger__.log(self.__logger__.DEBUG,  self.currentSubTopic + " Subscribed")
        self.currentTopicCount = self.currentTopicCount + 1
        self.__Subscribe__()

    #Mqtt On message recieved Callback
    def __On_Message__(self,client, obj, msg):
        str_data = str(msg.payload.decode("utf-8"))
        #retrive the last element from complete topic string 
        topic_str = msg.topic.split('/')[-1]
        
        #if a callback is registered on this topic 
        if self.__msg_rcv_callback__.get(topic_str) != None:
            self.__msg_rcv_callback__[topic_str](str_data)

    def __Connect__(self):
        """
        Use this function to Connect the mqtt client
        """
        host        = self.__configs__["HOST_ADDRESS"]
        port        = self.__configs__["PORT"]
        keepAlive   = self.__configs__["KEEP_ALIVE_INTERVAL"]
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
            self.MakeSubscriptionMap()
            self.__logger__.log(self.__logger__.DEBUG,'MQTT Client Connected Successfully')
            
            if self.isReconnected == False:
                self.__Subscribe__()    
            self.isReconnected = False
            
        else :
            self.__logger__.log(self.__logger__.ERROR, 'Failed to Connect MQTT Client, Reason : ' + str(rc))
            self.__On_Disconnect__(self.__mqttClient__, '',-1)

    def PublishLiveData(self, data):
        ret = False
        if self.IsConnected():

            topic = self.__Get_Subscription_Topic__(topic ='live')

            rc = self.__mqttClient__.publish(topic, data)
            if rc.rc ==  mqtt.MQTT_ERR_SUCCESS:
                self.__logger__.log(self.__logger__.DEBUG, 'Message Published Successfully Topic = ' + topic +' Payload = ' + data , True)
                ret = True
            else:
                self.__logger__.log(self.__logger__.DEBUG, 'Failed to Publish Data | Topic = ' + topic +' Payload = ' + data )
                self.__On_Disconnect__(self.__mqttClient__,'',5)
        else:
            self.__MessageQueue__['live'] = data
        
        return ret

    def Publish(self, data):
        ret = False
        if self.IsConnected():
            #change for future
            topic = self.__default_status_topic__

            rc = self.__mqttClient__.publish(topic, data)
            if rc.rc ==  mqtt.MQTT_ERR_SUCCESS:
                self.__logger__.log(self.__logger__.DEBUG, 'Message Published Successfully Topic = ' + topic +' Payload = ' + data, True )
                ret = True
            else:
                self.__logger__.log(self.__logger__.DEBUG, 'Failed to Publish Data | Topic = ' + topic +' Payload = ' + data )
        else:
            elf.__MessageQueue__['status'] = data
        return ret

    def Connect(self):
        """
        Start mqtt client to connect and subscribe
        """
        self.__Connect__();

    def Process(self):
        self.__mqttClient__.loop()
        ret, topic = False, ' '
        if 'live' in self.__MessageQueue__:
            ret = self.PublishLiveData(self.__MessageQueue__['live'])
            topic = 'live'
        elif 'status' in self.__MessageQueue__:
            ret = self.Publish(self.__MessageQueue__['status'])
            topic = 'status'

        if ret == True:
            del(self.__MessageQueue__[topic]) 
