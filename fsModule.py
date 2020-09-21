import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from datetime import datetime
import pytz

import csv
import sys

# Notes
    # Update Machine's sensors metadata
    # [V] Added MachineParentDocID when creating new sensor (createSensor)
    # [V] createSensor will only create an initial metadata on ParentMachine doc.
    # [V] Implemented getSensorParentDocID
    # [V] Update machine's sensor metadata when adding new sensor data (addSensorDataRow)
    # [ ] Create a functionality to update sensor metadata based on latest existing data (refreshSensorMetadatas)

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
            u'name'             : machineName,
            u'desc'             : machineDesc,
            u'imgUrl'           : machineImgUrl,
            u'sensorsMetadata'  : []
        }

        ref = parentRef.add(data)

        newDocID = ref[1].id

        # Update ProdLines Metadata
        self.updateMachinesMetadata(companyID,factoryID,prodLineID,machineName,machineDesc,machineImgUrl, newDocID)

        return newDocID

    def createSensor(self, companyID, factoryID, prodLineID, machineID, sensorName, sensorTagID, sensorData=None):
        """ Write a new sensor document in "Sensors" root collection. Returns newly created DocID
        
        Then, will set an initial sensor metadata in parent's (machine) document. (without actual sensor numerical data"""

        # if sensorData is None:
        #     # For some reason, Firestore doesn't support server timestamp to be put inside Array.
        #     # Temp Fix: Use client timestamp

        #     # Dummy data
        #     t = datetime.now(tz=pytz.timezone('Asia/Jakarta'))

        #     sensorData = {
        #         u'_timestamp': t,
        #         u'batt': 0,
        #         u'peak_x': 0,
        #         u'peak_y': 0,
        #         u'peak_z': 0,
        #         u'rms_x': 0,
        #         u'rms_y': 0,
        #         u'rms_z': 0,
        #         u'temp': 0,
        #         u'fft':'1,1,1;2,2,2;3,3,3;'
        #     }

        parentRef = self.db.collection("Sensors")

        machineParentDocID = "Companies/{}/Factories/{}/ProdLines/{}/Machines/{}".format(companyID,factoryID,prodLineID,machineID)

        data = {
            u'name'                 : sensorName,
            u'SensorTagID'          : sensorTagID,
            u'ParentMachineDocID'   : machineParentDocID,
            u'data'                 : []
        }

        ref = parentRef.add(data)
        
        newDocID = ref[1].id

        # Update Machine's Sensor Metadata (with no data)
        self.addInitialSensorsMetadata(machineParentDocID,sensorName,sensorTagID,newDocID)

        return newDocID

    # Read

    def getSensorParentDocID(self, sensorID):
        """Returns a complete address of the given sensor's MachineParentDocID from 'Sensors' collection."""

        resDict = fa.fs.readDocument("Sensors/{}".format(sensorID))

        return resDict['ParentMachineDocID']

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
        return doc.to_dict()

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

    def addInitialSensorsMetadata(self, parentMachineDocID, sensorName, sensorTagID, sensorID, sensorData=None):
        """Set initial metadata (No numerical data) of a Machine's Sensors Metadata"""

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

        parentRef = self.db.document(parentMachineDocID)

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

    def refreshSensorMetadata(self, sensorID):
        """Takes a Sensor Document ID, Get the latest data row, and push it to MachineParent's Metada"""

        # Get sensors data
        dataRows = self.readDocument("Sensors/{}".format(sensorID))['data']

        # Sort by latest first
        dataRows = sorted(dataRows, key = lambda i: i['_timestamp'], reverse=True)

        # Copy latest data to ParentMachine's metadata
        self.updateSensorMetadata(sensorID, dataRows[0])
        return

    def updateSensorMetadata(self, sensorID, sensorData):
        """Updates latest sensor data of a Machine's Sensors Metadata"""

        # Get current sensor metadata from MachineParent 
        parentMachineDocID = self.getSensorParentDocID(sensorID)
        parentRef = self.db.document(parentMachineDocID)
        listOfMetadata = parentRef.get().to_dict()['sensorsMetadata']

        # Find the sensor to be updated (by Document ID)
        dataIndex = self.findElementFromListOfDicts(listOfMetadata,"_SensorID", sensorID)
        targetData = listOfMetadata[dataIndex]

        # Delete the old data from the list
        del listOfMetadata[dataIndex]

        # (Locally) update sensor metadata
        targetData['_timestamp'] = sensorData['_timestamp']
        targetData['batt'] = sensorData['batt'] 
        targetData['peak_x'] = sensorData['peak_x'] 
        targetData['peak_y'] = sensorData['peak_y'] 
        targetData['peak_z'] = sensorData['peak_z'] 
        targetData['rms_x'] = sensorData['rms_x'] 
        targetData['rms_y'] = sensorData['rms_y'] 
        targetData['rms_z'] = sensorData['rms_z'] 
        targetData['temp'] = sensorData['temp'] 

        # Re-append newly updated metadata to list
        listOfMetadata.append(targetData)

        # Post the new list to db
        data = {
            'sensorsMetadata' : listOfMetadata
        }
        parentRef.update(data)
    
    def addSensorDataRow(self, sensorID, data, newData=False):
        """Push a row of data to a given sensorID.
        
        If newData, will also update the machine's sensor metadata using given sensor datarow"""
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

        if isinstance(data, list):
            print("Data must be a single dict containing one row of data")
            return False

        # Step one, push sensor data to sensor doc 
        sensorRef = self.db.document("Sensors/{}".format(sensorID))

        sensorRef.update({
            'data': firestore.ArrayUnion([data])
        })

        
        # Step two, if data is new, update the metadata on ParentMachineDoc
        if(newData == True):
            self.updateSensorMetadata(sensorID,data)

    def addSensorDataRows(self, sensorID, data):
        """Pushes a List of Sensor Data rows to a specified Sensor Document.
        
        Also refreshes the ParentMachine's metadata to its latest sensor datarow"""
        parentRef = self.db.document("Sensors/{}".format(sensorID))

        parentRef.update({
            'data': firestore.ArrayUnion(data)
        })

        self.refreshSensorMetadata(sensorID)

    # Helper Function

    def findElementFromListOfDicts(self, listOfDicts, keyToMatch, valueToMatch):
        """Returns the index of a specified Dict inside a given ListOfDicts based on given key and value to match"""
        for i in range(len(listOfDicts)): 
            if listOfDicts[i][keyToMatch] == valueToMatch: 
                return i
                break
            
        return None
