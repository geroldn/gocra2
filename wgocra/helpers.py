import xmltodict

class ExternalMacMahon:
    def s_import(self, file):
        self.doc = xmltodict.parse(file.read())
        return True

    def import2(self, memfile):
        self.s_import(memfile)
        return self
