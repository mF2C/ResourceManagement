class InformationElementAttribute(object):
    #definition of the different hex codes for each service type
    SERVICE_TYPE_DICT =  {"01":"High storage", "02":"Medium storage", "03":"Low storage","04":"High bandwidth", "05":"Medium bandwidth", "06":"Low bandwidth", "07":"High processing", "08":"Medium processing", "09":"Low processing"}
    #definition of the different hex codes for each urgency level
    URGENCY_DICT = {"01":"HIGH","02":"MEDIUM", "03":"LOW"}
    #definition of the hex codes of the different VSIE attributes
    TYPES = {"01": "Leader ID","02":"Service type", "03":"Reward", "04": "Urgency level"}
    
    SERVICE_TYPE_DICT_SWAPPED = {y:x for x,y in SERVICE_TYPE_DICT.items()}
    URGENCY_DICT_SWAPPED = {y:x for x,y in URGENCY_DICT.items()}
    TYPES_SWAPPED = {y:x for x,y in TYPES.items()}
    
    def __init__(self, type, value) :
      self.type = type
      self.value = value
    
    @staticmethod
    def get_type_name(t): 
        
        return InformationElementAttribute.TYPES[t]
        
    def get_type(self): 
        return self.type
    
    def set_type(self, type):
        self.type = type
    
    def get_length(self): #example value: a1b2c3d4a1b2c3d4 It represents the hexadecimal: a1:b2:c3:d4:a1:b2:c3:d4 whose length in bytes is 8
        #so for our initial value we calculate the length of the string and divide by 2 since each two characters represents one byte
        #the obtained value is decimal, so we convert it to hex
        return hex(int(len(self.value) / 2))[2:].zfill(2)
    
    def set_length(self, length):
        self.length = length
    
    def get_value(self): 
        return self.value
    
    def set_value(self, value):
        self.value = value

    @staticmethod
    def get_attribute_dict(attribute): 
        
        #example: 020104 which represents the hex 02:01:04 => type is the first byte 
        #then to get it the first 2 characters are extracted
        type = attribute[0:2]
        #then, the dict will be filled with the human-readable type name, e.g. "Service type" for the example above
        #and the human-readable value, e.g. "High bandwidth" for the example above
        if type not in InformationElementAttribute.TYPES.keys():
            dict = {"type": "Unsupported type","value":"Unsupported"}
        else:
            if type == "01":
                dict = {"type": InformationElementAttribute.get_type_name(attribute[0:2]), "value":attribute[4:]}
            else:
                dict = {"type": InformationElementAttribute.get_type_name(attribute[0:2]), "value":InformationElementAttribute.convert_value_from_hex(attribute[0:2],attribute[4:])}
        return dict
    
    @staticmethod
    def convert_value_from_hex(type,value): #decodes and returns the human-readable value of the attribute's value 
        if type == "02":
            if value in InformationElementAttribute.SERVICE_TYPE_DICT.keys():
                return InformationElementAttribute.SERVICE_TYPE_DICT[value]
            else : 
                return "Unknown/Incorrect service type"
        else:
            if type == "03":
                return str(int(value, 16))+"EUR"
            else:
                if type == "04":
                    if value in InformationElementAttribute.URGENCY_DICT.keys():                  
                        return InformationElementAttribute.URGENCY_DICT[value]
                    else:
                        return "Unknown/Incorrect urgency level"
    @staticmethod
    def convert_value_to_hex(type,value):
        if type == "02":
            return InformationElementAttribute.SERVICE_TYPE_DICT_SWAPPED[value]
        else:
            if type == "03":
                return hex(int(value))[2:].zfill(2)
            else:
                if type == "04":
                    return InformationElementAttribute.URGENCY_DICT_SWAPPED[value]