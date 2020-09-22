import fsModule
import authModule

class DevApp:
    """This class serves as the interface of fsModule (CLI Input)"""
    def __init__(self):
        self.fs = fsModule.FsModule()
        self.auth = authModule.AuthModule()
        self.companyRef     = ''
        self.factoryRef     = ''
        self.prodLineRef    = ''
        self.machineRef     = ''
        self.sensorRef      = ''

    # Functions

    def setupNewCompany(self):
        """A tool to create a new company and all its sublevels"""

        print("--- Welcome to Vibsense Company Creator ---\n")

        # Company
        cName = input("Please Input Your Company Name: \n")
        cRef = self.fs.createCompany(cName)
        print("Created company {} ({})\n".format(cName, cRef))

        # Factory
        fName = input("Please Input Factory Name: \n")
        fRef = self.fs.createFactory(cRef, fName)
        print("Created factory {} ({})\n".format(fName, fRef))

        # ProdLine
        pName = input("Please Input ProdLine Name: \n")
        pRef = self.fs.createProdLine(cRef, fRef, pName)
        print("Created ProdLine {} ({})\n".format(pName, pRef))

        # Machine
        mName = input("Please Input Machine Name: \n")
        mRef = self.fs.createMachine(cRef, fRef, pRef, mName)
        print("Created Machine {} ({})\n".format(mName, mRef))

        # Sensor
        sName   = input("Please Input Sensor Name: \n")
        sTag    = input("Please Input Sensor Hexadecimal Tag: \n")
        sRef = self.fs.createSensor(cRef,fRef, pRef, mRef, sName, sTag)
        print("Created Sensor {} ({})\n".format(sName, sRef))

        # SensorData
        confirmInput = input("Do you want to add data to {} ({}) ? (y/n)".format(sName, sRef))
        if(confirmInput == 'y'):
            dataSrc = input("Please input the data source filename (csv): \n")
            self.addSensorDataRows(sRef,dataSrc)

    def addSensorDataRows(self, sensorID, dataFileName):
      """Pushes multiple data-rows of a sensor (given the docID)"""
      dataRows = self.parseSensorData(dataFileName)

      self.fs.addSensorDataRows(sensorID,dataRows)

    def addSensorDataRow(self, sensorID, sensData):
        """Pushes a single data-row of a sensor (given the DocID)"""

        # sensData example
        # t = datetime.now(tz=pytz.timezone('Asia/Jakarta'))
        # sensorData = {
        #             '_timestamp': t,
        #             'batt': 3.333,
        #             'peak_x': 5.555,
        #             'peak_y': 4.444,
        #             'peak_z': 8.888,
        #             'rms_x': 2.222,
        #             'rms_y': 2.222,
        #             'rms_z': 2.222,
        #             'temp': 66.66,
        #             'fft':None
        #         }
        self.fs.addSensorDataRow(sensorID,sensData,True)

    def setupNewUser(self):

        # Account Creation
        uEmail  = input("Please Input Email: \n")
        uPw     = input("Please Input Password: \n")
        uid     = self.auth.createUser(uEmail, uPw)
        print("\nCreated account {} ({})\n".format(uEmail, uid))

        # Show company list
        index = 0
        companyList = self.fs.getAllCompanies()
        print("Choose a company to associate the user with:")

        for c in companyList:
            print("[{}] {} ({})".format(index, c['name'], c['id']))
            index = index + 1
        choice  = int(input("Input Company Index: "))

        # Link Account to a Company
        self.fs.addUserToCompany(companyList[choice]['id'], uid)
        print("\nLinked account ({}) to company ({}) \n".format(uEmail, companyList[choice]['name']))


    # Helper function

    def parseSensorData(self, fileName):
        """Take SensorData(.csv) file location as param and returns a list of dicts of SensorData"""

        #    0         1       2      3     4       5        6      7      8      9 
        # sens_id, timestamp, batt, temp, x_peak, y_peak, z_peak, x_rms, y_rms, z_rms
        fields = []
        rows = []

        result = []

        with open(fileName, 'r') as csvfile: 
            csvreader = csv.reader(csvfile) 
            
            fields = next(csvreader) 
        
            for row in csvreader: 
                rows.append(row)
      
        for row in rows:
            data = {
                u'_timestamp': datetime.strptime(row[1], '%m/%d/%Y %H:%M'),
                u'batt': float(row[2]),
                u'peak_x': float(row[4]),
                u'peak_y': float(row[5]),
                u'peak_z': float(row[6]),
                u'rms_x': float(row[7]),
                u'rms_y': float(row[8]),
                u'rms_z': float(row[9]),
                u'temp': float(row[3]),
                u'fft': None
            }

            result.append(data)

        # print(result)

        return result


dev = DevApp()

# dev.setupNewUser()

# sensData example
    # t = datetime.now(tz=pytz.timezone('Asia/Jakarta'))
    # sensorData = {
    #             '_timestamp': t,
    #             'batt': 3.333,
    #             'peak_x': 5.555,
    #             'peak_y': 4.444,
    #             'peak_z': 8.888,
    #             'rms_x': 2.222,
    #             'rms_y': 2.222,
    #             'rms_z': 2.222,
    #             'temp': 66.66,
    #             'fft':None
    #         }

# dev.addSensorDataRow("lOWj7bWGrMtxhw9hwvJo", sensorData)

# dev.setupNewCompany()