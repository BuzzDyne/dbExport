import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin.firestore import SERVER_TIMESTAMP

from datetime import datetime
import pytz

import csv
import sys

# v3 = changed the document layout for React Integration
    # All c,f, and p fields name changed to be same as each others
      # "CompanyName", "FactoryName", "ProdLineName" > "name", etc 
    # Every child metadata of levels mentioned above is changed to "childrenMetadata" (along with its fields)
      # "factoryID" -> "childID"

# TODOS
#   - Adding Sensor Data doesnt update the sensorsMetadata field in "Machine" docs
#   - Currently document in Sensors/ collection can exceed the limit of 1MB per document
# 

# NOTES
#   - Push UTC+7 Timezone (pytz) to Firestore, 
#         If unaware datetime is push, firestore will assume it is UTC+0 


cred = credentials.Certificate("vibsensedup-firebase-adminsdk-uzlnm-c655ba999f.json")

class FsModule:
    """Handles CRUD operation to the Firestore DB
    
    Requires Firestore's JSON Auth Key to be placed on the same dir as this module"""
    def __init__(self):
        firebase_admin.initialize_app(cred)        
        self.db = firestore.client()


    # Create

    def createCompany(self, companyName, registeredUserIDs=None):
        """ Write a new company document to "Companies" root collection. Returns newly created DocID"""

        target = "Companies"

        if registeredUserIDs is None:
            registeredUserIDs = []

        data = {
            u'name'      : companyName,
            u'childrenMetadata': [],
            u'registeredUserIDs': registeredUserIDs
        }

        ref = self.db.collection(target).add(data)

        return ref[1].id

    def createFactory(self, companyID, factoryName, factoryDesc=None, factoryImgUrl=None):
        """ Write a new factory document in "Factories" subcollection of a specified parent CompanyID. Returns newly created DocID"""

        if factoryDesc is None:
            factoryDesc = "This is a default short description for a factory"
        if factoryImgUrl is None:
            factoryImgUrl = "https://iii.vibsense.net/static/admin/files/img/GwoOjLQQkJNgnAOu.jpg"
        
        # parentRef = self.db.collection("Companies").document(companyParentID).collection("Factories")
        parentRef = self.db.collection("Companies/{}/Factories".format(companyID))

        data = {
            u'name'          : factoryName,
            u'desc'          : factoryDesc,
            u'imgUrl'        : factoryImgUrl,
            u'childrenMetadata'    : []
        }

        ref = parentRef.add(data)

        # Update Company Metadata
        self.updateFactoriesMetadata(companyID,factoryName,factoryDesc,factoryImgUrl,ref[1].id)

        return ref[1].id

    def createProdLine(self, companyID, factoryID, prodLineName, prodLineDesc=None, prodLineImgUrl=None):
        """ Write a new prodLine document in "ProdLines" subcollection of a specified parent FactoryID. Returns newly created DocID"""

        if prodLineDesc is None:
            prodLineDesc = "This is a default short description for a product line"
        if prodLineImgUrl is None:
            prodLineImgUrl = "https://iii.vibsense.net/static/admin/files/img/GwoOjLQQkJNgnAOu.jpg"
        
        parentRef = self.db.collection("Companies/{}/Factories/{}/ProdLines".format(companyID, factoryID))

        data = {
            u'name'         : prodLineName,
            u'desc'         : prodLineDesc,
            u'imgUrl'       : prodLineImgUrl,
            u'childrenMetadata'     : []
        }

        ref = parentRef.add(data)

        newDocID = ref[1].id

        # Update ProdLines Metadata
        self.updateProdLinesMetadata(companyID,factoryID,prodLineName,prodLineDesc,prodLineImgUrl, newDocID)

        return newDocID

    def createMachine(self, companyID, factoryID, prodLineID, machineName, machineDesc=None, machineImgUrl=None):
        """ Write a new machine document in "Machines" subcollection of a specified parent ProdLineID. Returns newly created DocID"""

        if machineDesc is None:
            machineDesc = "This is a default short description for a product line"
        if machineImgUrl is None:
            machineImgUrl = "https://iii.vibsense.net/static/admin/files/img/GwoOjLQQkJNgnAOu.jpg"
        
        parentRef = self.db.collection("Companies/{}/Factories/{}/ProdLines/{}/Machines".format(companyID, factoryID, prodLineID))

        data = {
            u'name'         : machineName,
            u'desc'         : machineDesc,
            u'imgUrl'       : machineImgUrl,
            u'childrenMetadata'     : []
        }

        ref = parentRef.add(data)

        newDocID = ref[1].id

        # Update ProdLines Metadata
        self.updateMachinesMetadata(companyID,factoryID,prodLineID,machineName,machineDesc,machineImgUrl, newDocID)

        return newDocID

    def createSensor(self, companyID, factoryID, prodLineID, machineID, sensorName, sensorTagID, sensorData=None):
        """ Write a new sensor document in "Sensors" root collection. Returns newly created DocID"""

        if sensorData is None:
            # For some reason, Firestore doesn't support server timestamp to be put inside Array.
            # Temp Fix: Use client timestamp

            # Dummy data
            t = datetime.now(tz=pytz.timezone('Asia/Jakarta'))

            sensorData = {
                u'_timestamp': t,
                u'batt': 3.6,
                u'peak_x': 2.1,
                u'peak_y': 2.1,
                u'peak_z': 2.1,
                u'rms_x': 1.24,
                u'rms_y': 1.24,
                u'rms_z': 1.24,
                u'temp': 45.44,
                u'fft':'4,4,2;2,2,1;3,3,2;'
            }

        parentRef = self.db.collection("Sensors")

        data = {
            u'name'           : sensorName,
            u'SensorTagID'          : sensorTagID,
            u'data'                 : [sensorData]
        }

        ref = parentRef.add(data)
        
        newDocID = ref[1].id

        # Update ProdLines Metadata
        self.updateSensorsMetadata(companyID,factoryID,prodLineID,machineID,sensorName,sensorTagID,newDocID)

        return newDocID

    # Read

    def readCompany(self, companyName=None, docID=None):
        """ Get a company document by either its Name or DocID

        Returns a 'dict' or 'None' if not found 
        """

        target = "Companies"

        companiesCol = self.db.collection(target)

        if companyName is None and docID is None:
            # No params given, returning
            return None
        elif companyName is not None:
            # query by Name
            docs = companiesCol.where("name", "==", companyName).stream()

            my_dict = { el.id: el.to_dict() for el in docs }
            
            if(my_dict == {}):
                return None

            return my_dict
        else:
            # get by DocID
            try:
                doc = companiesCol.document(docID).get()
                my_dict = {doc.id: doc.to_dict()}

                if(my_dict[doc.id] == None):
                    return None

                return my_dict
            except:
                print("Exception encountered")
                return None

    def readDocument(self, target):
        # doc_ref = self.db.document(target)
        # doc = doc_ref.get()
        # my_dict = {doc.id: doc.to_dict()}
        # print(my_dict)

        doc = self.db.document(target).get() 
        return {doc.id: doc.to_dict()}

    # Update

    def updateFactoriesMetadata(self, companyID, factoryName, factoryDesc, factoryImgUrl, factoryID):
        """Updates metadata of a Company's Factories Metadata"""

        parentRef = self.db.document("Companies/{}".format(companyID))

        parentRef.update({
            u'childrenMetadata': firestore.ArrayUnion([{
                u'childName': factoryName,
                u'childDesc': factoryDesc,
                u'childImgUrl': factoryImgUrl,
                u'_childID': factoryID
            }])
        })

    def updateProdLinesMetadata(self, companyID, factoryID, prodLineName, prodLineDesc, prodLineImgUrl, prodLineID):
        """Updates metadata of a Factory's ProductLines Metadata"""

        parentRef = self.db.document("Companies/{}/Factories/{}".format(companyID, factoryID))

        parentRef.update({
            u'childrenMetadata': firestore.ArrayUnion([{
                u'childName': prodLineName,
                u'childDesc': prodLineDesc,
                u'childImgUrl': prodLineImgUrl,
                u'_childID': prodLineID
            }])
        })

    def updateMachinesMetadata(self, companyID, factoryID, prodLineID, machineName, machineDesc, machineImgUrl, machineID):
        """Updates metadata of a ProdLine's Machines Metadata"""

        parentRef = self.db.document("Companies/{}/Factories/{}/ProdLines/{}".format(companyID, factoryID, prodLineID))

        parentRef.update({
            u'childrenMetadata': firestore.ArrayUnion([{
                u'childName': machineName,
                u'childDesc': machineDesc,
                u'childImgUrl': machineImgUrl,
                u'_childID': machineID
            }])
        })

    def updateSensorsMetadata(self, companyID, factoryID, prodLineID, machineID, sensorName, sensorTagID, sensorID, sensorData=None):
        """Updates metadata of a Machine's Sensors Metadata"""

        # Dummy Sensor Data
        if sensorData is None:
            sensorData = {
                '_timestamp': None,
                'batt': None,
                'peak_x': None,
                'peak_y': None,
                'peak_z': None,
                'rms_x': None,
                'rms_y': None,
                'rms_z': None,
                'temp': None,
                'fft':None
            }

        parentRef = self.db.document("Companies/{}/Factories/{}/ProdLines/{}/Machines/{}".format(companyID, factoryID, prodLineID, machineID))

        parentRef.update({
                'sensorsMetadata': firestore.ArrayUnion([{
                    'sensorName': sensorName,
                    'sensorTagID': sensorTagID,
                    '_timestamp': sensorData["_timestamp"],
                    'batt': sensorData["batt"],
                    'peak_x': sensorData["peak_x"],
                    'peak_y': sensorData["peak_y"],
                    'peak_z': sensorData["peak_z"],
                    'rms_x': sensorData["rms_x"],
                    'rms_y': sensorData["rms_y"],
                    'rms_z': sensorData["rms_z"],
                    'temp': sensorData["temp"],
                    '_SensorID': sensorID
            }])
        })
    
    def addSensorDataRow(self, sensorID, data=None, newData=True):
        """Push a row of data to a given sensorID.
        
        If newData, will also update the metadata"""
        # sensorData = {
        #     '_timestamp': None,
        #     'batt': 3.654,
        #     'peak_x': 5.052,
        #     'peak_y': 4.982,
        #     'peak_z': 8.565,
        #     'rms_x': 2.465,
        #     'rms_y': 2.548,
        #     'rms_z': 2.859,
        #     'temp': 65.56,
        #     'fft':None
        # }

        if data is None and isinstance(data, list):
            print("Data is either Empty or a List")
            return False
        
        parentRef = self.db.document("Sensors/{}".format(sensorID))

        parentRef.update({
            'data': firestore.ArrayUnion([data])
        })

    def addSensorDataRows(self, sensorID, data=None):
        if data is None:
            return False
        
        parentRef = self.db.document("Sensors/{}".format(sensorID))

        parentRef.update({
            'data': firestore.ArrayUnion(data)
        })


class FsApp:
    """This class serves as the interface of fsModule (CLI Input)"""
    def __init__(self):
        self.fm = FsModule()
        self.companyRef     = ''
        self.factoryRef     = ''
        self.prodLineRef    = ''
        self.machineRef     = ''
        self.sensorRef      = ''

    def setupNewCompany(self):
        print("--- Welcome to Vibsense Company Creator ---\n")

        # Company
        cName = input("Please Input Your Company Name: \n")
        cRef = self.fm.createCompany(cName)
        print("Created company {} ({})\n".format(cName, cRef))

        # Factory
        fName = input("Please Input Factory Name: \n")
        fRef = self.fm.createFactory(cRef, fName)
        print("Created factory {} ({})\n".format(fName, fRef))

        # ProdLine
        pName = input("Please Input ProdLine Name: \n")
        pRef = self.fm.createProdLine(cRef, fRef, pName)
        print("Created ProdLine {} ({})\n".format(pName, pRef))

        # Machine
        mName = input("Please Input Machine Name: \n")
        mRef = self.fm.createMachine(cRef, fRef, pRef, mName)
        print("Created Machine {} ({})\n".format(mName, mRef))

        # Sensor
        sName   = input("Please Input Sensor Name: \n")
        sTag    = input("Please Input Sensor Hexadecimal Tag: \n")
        sRef = self.fm.createSensor(cRef,fRef, pRef, mRef, sName, sTag)
        print("Created Sensor {} ({})\n".format(sName, sRef))

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

    def injectSensorData(self, sensorID, dataFileName):
      dataRows = self.parseSensorData(dataFileName)

      # for row in dataRows:
      #   self.fm.addSensorDataRow(sensorID, data=row)
      
      self.fm.addSensorDataRows(sensorID,dataRows)

      print("Sensor updated.")



fa = FsApp()

# fa.injectSensorData('g3weXncGUMkRPr2I9whg','sens_data.csv')

sensorData = {
            '_timestamp': None,
            'batt': 3.654,
            'peak_x': 5.052,
            'peak_y': 4.982,
            'peak_z': 8.565,
            'rms_x': 2.465,
            'rms_y': 2.548,
            'rms_z': 2.859,
            'temp': 65.56,
            'fft':None
        }

fa.fm.addSensorDataRow("g3weXncGUMkRPr2I9whg", sensorData)


# fa.setupNewCompany()

# Testing for FsModule (Use the FsApp)

# fm = fsModule()
# fm.readDocument('Companies/rDAeKWkR5cvn9SClJr9l/Factories/1po9D8ZjPnyPWlEhK0wC/ProdLines/jjxeOGYTeLnr5IwTXerO/Machines/ZwCO2wlCm0v8iRcNufr2/Sensors/KKM0WbBsESWQNFvdO4mM')
# fm.createCompany('deleteCompany')
# fm.updateFactoriesMetadata("rDAeKWkR5cvn9SClJr9l", "newFacName", "facDesc", "url", "facID")
# fm.readCompany(docID='rDAeKWkR5cvn9SClJr9l')
# fm.createFactory("rDAeKWkR5cvn9SClJr9l", "AutoMD")
# fm.createProdLine('rDAeKWkR5cvn9SClJr9l','1po9D8ZjPnyPWlEhK0wC', "PM Super")
# fm.createMachine('rDAeKWkR5cvn9SClJr9l','1po9D8ZjPnyPWlEhK0wC', 'jjxeOGYTeLnr5IwTXerO', "Super Dryer Machine")
# fm.createSensor('rDAeKWkR5cvn9SClJr9l','1po9D8ZjPnyPWlEhK0wC', 'jjxeOGYTeLnr5IwTXerO', 'ZwCO2wlCm0v8iRcNufr2', "Bottom Back Sensor", 'caca')
# fm.createSensor('rDAeKWkR5cvn9SClJr9l','icNXB9Gk5mLWrGWuBVBQ', 'TmScIiPEWf3r3YwHpVVN', 'VjUUaygQq9DaNA74bOcu','TIMESTAMP Sensor','DDDD')
# fm.updateSensorsMetadata("rDAeKWkR5cvn9SClJr9l", "icNXB9Gk5mLWrGWuBVBQ", "TmScIiPEWf3r3YwHpVVN", "VjUUaygQq9DaNA74bOcu", "SName", "2CAC", "asdascsacascascsa" )