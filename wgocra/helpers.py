import xmltodict

class ExternalMacMahon:
    def s_import(self, file):
        self.doc = xmltodict.parse(file.read())
        return True

    def xml_import(self, memfile):
        self.s_import(memfile)
        return self
