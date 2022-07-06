import 

def cleanText(self, text_data_in_list):
    text = re.sub('[-=+#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]','', text_data)
    return text
