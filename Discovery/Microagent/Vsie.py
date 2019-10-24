class Vsie(object): 
    
    ELEMENT_ID = "dd"
    OUI = "ff22cc"
    
    def __init__(self, vendor_specific_content) :
        self.vendor_specific_content = vendor_specific_content

    @staticmethod
    def caculate_vsie_length(self):
        #print("calculating vsie_length")
        s = 0
        for item in self.vendor_specific_content:#for example 01067a64696e6562
            s += int(item.get_length(), 16) +1+1 #first we convert the attribute's length from hex to decimal 
            #then we add +1 for the 1st byte representing the type and +1 for the 2nd byte representing the length
        s += 3 #we add the oui length, the obtained length is decimal
        return hex(s)[2:].zfill(2) #so, we convert it back to hex

    def set_length(self, length):
        self.length = length

    def set_vendor_specific_content(self, vendor_specific_content):
        self.vendor_specific_content.vendor_specific_content
       
    @staticmethod
    def get_vendor_specific_content(payload):  # Example Input: 01 06 7a 65 69 6e 65 62 02 01 02 04 01 01
        attribute_list = []
        payload = payload.replace(" ", "")
        while payload:
            l = payload[2:4]
            i = int(l, 16)
            j = 4 + 2 * i
            attribute_list.append(payload[0:j])
            payload = payload[j:]
            
        return attribute_list #example output: ['01067a64696e6562','020102', '040101']

    def create_mf2c_vsie_hex(self): #puts the vsie in the correct format expected by the vendor_elements field of hostapd.conf
     
        s = self.ELEMENT_ID + Vsie.caculate_vsie_length(self) + self.OUI 
        for item in self.vendor_specific_content:
            s += item.get_type()
            s += item.get_length()
            s += item.get_value()
        return s
